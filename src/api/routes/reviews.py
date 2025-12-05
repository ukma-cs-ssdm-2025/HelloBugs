from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import g
from src.api.auth import token_required
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
    get_average_rating
)
from src.api.db import db

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
        new_review['user_id'] = current_user.user_id

        try:
            review = create_review(db, new_review)
            return review
        except ValueError as e:
            if "not found" in str(e).lower():
                abort(404, message=str(e))
            else:
                abort(400, message=str(e))


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
            
            if review['user_id'] != current_user.user_id and current_user.role != 'ADMIN':
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
            
            if review['user_id'] != current_user.user_id and current_user.role != 'ADMIN':
                abort(403, message="Ви не маєте прав для видалення цього відгуку")
            
            delete_review(db, review_id)
            return "", 204
        except ValueError as e:
            abort(400, message=str(e))
