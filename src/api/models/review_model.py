from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.api.db import Base


class Review(Base):
    """Model for hotel reviews"""
    __tablename__ = 'reviews'

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.room_id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', backref='reviews')
    room = relationship('Room', backref='reviews')

    def __repr__(self):
        return f'<Review {self.review_id} by User {self.user_id}>'

    def to_dict(self):
        """Convert review to dictionary"""
        return {
            'review_id': self.review_id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name
            } if self.user else None,
            'room': {
                'room_number': self.room.room_number,
                'room_type': self.room.room_type
            } if self.room else None
        }
