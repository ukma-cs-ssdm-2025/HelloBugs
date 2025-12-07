from src.api.models.review_model import Review
from src.api.models.user_model import User
from datetime import datetime


def get_all_reviews(db):
    """Get all reviews"""
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    return reviews


def get_review_by_id(db, review_id):
    """Get a specific review by ID"""
    review = db.query(Review).get(review_id)
    return review


def get_user_reviews(db, user_id):
    """Get all reviews by a specific user"""
    reviews = db.query(Review).filter_by(user_id=user_id).order_by(Review.created_at.desc()).all()
    return reviews


def create_review(db, review_data):
    """Create a new review"""
    user = db.query(User).get(review_data['user_id'])
    if not user:
        raise ValueError(f"User with ID {review_data['user_id']} not found")
    
    new_review = Review(
        user_id=review_data['user_id'],
        room_id=review_data['room_id'],
        rating=review_data['rating'],
        comment=review_data.get('comment')
    )
    
    db.add(new_review)
    db.commit()
    
    return new_review


def update_review(db, review_id, update_data):
    """Update an existing review"""
    review = db.query(Review).get(review_id)
    if not review:
        raise ValueError(f"Review with ID {review_id} not found")
    
    if 'rating' in update_data:
        review.rating = update_data['rating']
    if 'comment' in update_data:
        review.comment = update_data['comment']
    if 'room_id' in update_data:
        review.room_id = update_data['room_id']
    
    review.updated_at = datetime.utcnow()
    db.commit()
    
    return review


def delete_review(db, review_id):
    """Delete a review"""
    review = db.query(Review).get(review_id)
    if not review:
        raise ValueError(f"Review with ID {review_id} not found")
    
    db.delete(review)
    db.commit()
    
    return True


def get_average_rating(db):
    """Calculate average rating from all reviews"""
    from sqlalchemy import func
    avg_rating = db.query(func.avg(Review.rating)).scalar()
    return round(avg_rating, 1) if avg_rating else 0
