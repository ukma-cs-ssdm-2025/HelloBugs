from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import g
from src.api.auth import token_required, staff_required
from src.api.schemas.review_schema import (
    ReviewInSchema, ReviewOutSchema, ReviewPatchSchema
)
from src.api.services.review_service import (
    get_all_reviews,
    get_review_by_id,
    get_user_reviews,
    create_review,
    update_review,
    delete_review,
    get_average_rating,
    get_pending_reviews
)
from src.api.db import db
from src.api.models.user_model import UserRole
from werkzeug.exceptions import HTTPException

blp = Blueprint(
    "Reviews",
    "reviews",
    url_prefix="/api/v1/reviews",
    description="Operations on hotel reviews. Manage customer feedback and ratings."
)


@blp.route("/")
class ReviewList(MethodView):

    @blp.response(200, ReviewOutSchema(many=True), description="List of all reviews.")
    @blp.alt_response(500, description="Internal server error")
    def get(self):
        """Get all reviews"""
        return get_all_reviews(db)

    @blp.arguments(ReviewInSchema)
    @blp.response(201, ReviewOutSchema, description="Review created successfully.")
    @blp.alt_response(400, description="Invalid review data provided")
    @blp.alt_response(401, description="Authentication required")
    @blp.alt_response(404, description="User not found")
    @token_required
    def post(self, new_review):
        """Create a new review (requires authentication)"""
        current_user = g.current_user
        from src.api.models.user_model import UserRole
        if getattr(current_user, 'role', None) != UserRole.GUEST:
            abort(403, message="Лише гості можуть створювати відгуки")
        new_review['user_id'] = current_user.user_id

        try:
            review = create_review(db, new_review)
            return review
        except ValueError as e:
            if "not found" in str(e).lower():
                abort(404, message=str(e))
            else:
                abort(400, message=str(e))


@blp.route("/<int:review_id>/approve")
class ReviewApproval(MethodView):

    @blp.response(200, ReviewOutSchema, description="Review approved successfully")
    @blp.alt_response(401, description="Authentication required")
    @blp.alt_response(403, description="Staff/Admin access required or booking not found")
    @blp.alt_response(404, description="Review not found")
    @token_required
    @staff_required
    def post(self, review_id):
        """Approve review after verifying the user had a booking for the room"""
        try:
            review = get_review_by_id(db, review_id)
            if not review:
                abort(404, message=f"Review with ID {review_id} not found")

            # Verify booking exists for this user and room (not cancelled)
            from src.api.models.booking_model import Booking, BookingStatus
            booking = (
                db.query(Booking)
                  .filter(Booking.user_id == review.user_id)
                  .filter(Booking.room_id == review.room_id)
                  .filter(Booking.status != BookingStatus.CANCELLED)
                  .first()
            )
            if not booking:
                abort(403, message="Неможливо підтвердити відгук без наявного бронювання для цього номера")

            from src.api.services.review_service import approve_review
            approved = approve_review(db, review_id)
            return approved
        except ValueError as e:
            abort(400, message=str(e))


@blp.route("/pending")
class PendingReviews(MethodView):

    @blp.response(200, ReviewOutSchema(many=True), description="Pending reviews (staff only)")
    @blp.alt_response(401, description="Authentication required")
    @blp.alt_response(403, description="Staff/Admin access required")
    @token_required
    @staff_required
    def get(self):
        """Get list of reviews awaiting approval"""
        return get_pending_reviews(db)
@blp.route("/user/<int:user_id>")
class UserReviews(MethodView):

    @blp.response(200, ReviewOutSchema(many=True), description="User reviews")
    @blp.alt_response(500, description="Internal server error")
    def get(self, user_id):
        """Get all reviews by a specific user"""
        return get_user_reviews(db, user_id)


@blp.route("/average-rating")
class AverageRating(MethodView):

    @blp.response(200, description="Average rating")
    def get(self):
        """Get average rating from approved reviews"""
        avg_rating = get_average_rating(db)
        return {"average_rating": avg_rating}


@blp.route("/<int:review_id>")
class ReviewResource(MethodView):

    @blp.response(200, ReviewOutSchema, description="Review details retrieved successfully.")
    @blp.alt_response(404, description="Review not found")
    def get(self, review_id):
        """Get a specific review by ID"""
        review = get_review_by_id(db, review_id)
        if not review:
            abort(404, message=f"Review with ID {review_id} not found")
        # Незатверджені відгуки не повинні бути видимими публічно
        current_user = getattr(g, "current_user", None)
        user_role = getattr(current_user, "role", None)
        is_staff = user_role in (UserRole.STAFF, UserRole.ADMIN)
        is_owner = current_user and getattr(current_user, "user_id", None) == review.user_id
        if not review.is_approved and not (is_staff or is_owner):
            abort(404, message="Review is awaiting approval")
        return review

    @blp.arguments(ReviewPatchSchema)
    @blp.response(200, ReviewOutSchema, description="Review updated successfully")
    @blp.alt_response(400, description="Invalid review data provided")
    @blp.alt_response(401, description="Authentication required")
    @blp.alt_response(403, description="Not authorized to update this review")
    @blp.alt_response(404, description="Review not found")
    @token_required
    def patch(self, patch_data, review_id):
        """Update a review (user can update own review)"""
        current_user = g.current_user
        
        try:
            review = get_review_by_id(db, review_id)
            if not review:
                abort(404, message=f"Review with ID {review_id} not found")
            if review.user_id != current_user.user_id:
                abort(403, message="Ви не маєте прав для редагування цього відгуку")
            
            updated_review = update_review(db, review_id, patch_data)
            return updated_review
        except ValueError as e:
            abort(400, message=str(e))

    @blp.response(204, description="Review deleted successfully")
    @blp.alt_response(401, description="Authentication required")
    @blp.alt_response(403, description="Not authorized to delete this review")
    @blp.alt_response(404, description="Review not found")
    @token_required
    def delete(self, review_id):
        """Delete a review (user can delete own review, admin can delete any)"""
        current_user = g.current_user
        
        try:
            review = get_review_by_id(db, review_id)
            if not review:
                abort(404, message=f"Review with ID {review_id} not found")
            
            is_admin = getattr(current_user, 'role', None) == UserRole.ADMIN
            if review.user_id != current_user.user_id and not is_admin:
                abort(403, message="Ви не маєте прав для видалення цього відгуку")
            
            delete_review(db, review_id)
            db.commit()
            return "", 204
        except ValueError as e:
            db.rollback()
            abort(400, message=str(e))
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            import traceback
            print("[DELETE /reviews] Unexpected error:\n" + traceback.format_exc())
            abort(500, message="Internal server error")
