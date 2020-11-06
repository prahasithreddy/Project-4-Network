from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Follower(models.Model):
    """
    Represents a recursive User relationship. A User may be a follower of
    another User and/or have a group of Users following.
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='followers')

    class Meta:
        """
        A USer can of follow or be following another User once.
        """
        unique_together = ('follower', 'following')

    def __str__(self):
        return '{} is followed by {}'.format(self.follower, self.following)


class NetworkPost(models.Model):
    """
    Represents the content and meta information that make up a post.
    """
    content = models.TextField(max_length=10000)
    create_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="post_creator"
    )
    likes = models.ManyToManyField(
        "User",
        related_name="user_likes",
        blank=True
    )

    def total_likes(self):
        """
        Returns a count of likes for this post.
        """
        try:
            return self.likes.all().count()
        except ValueError:
            return None

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "creator_id": self.creator.id,
            "creator": self.creator.username,
            "create_date": self.create_date.strftime("%b %d %Y, %I:%M %p"),
            "likes": [user.id for user in self.likes.all()],
            "total_likes": self.total_likes()
        }
