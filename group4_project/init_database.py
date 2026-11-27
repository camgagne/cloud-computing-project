from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct
from aws_cdk import RemovalPolicy

S = dynamodb.AttributeType.STRING

# Class that defines a users table, follows table, posts table, likes table, and comments table
class DatabaseConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Users: one item per user. PK = Cognito sub id, no SK needed
        self.users_table = self._table("Users", pk="userId")
        self.users_table.add_global_secondary_index(	# gsi for username search
            index_name="byUsername", 
            partition_key=dynamodb.Attribute(name="searchBucket", type=S),   # searchBucket = "USER" always
            sort_key=dynamodb.Attribute(name="usernameLower", type=S),	# pass in username.lower() so capitalization doesn't affect search 
        )

        # Follows: one item per "A follows B".
        self.follows_table = self._table("Follows", pk="followerId", sk="followeeId")
        self.follows_table.add_global_secondary_index(	# gsi for finding who follows a certain user
            index_name="byFollowee",            
            partition_key=dynamodb.Attribute(name="followeeId", type=S),
            sort_key=dynamodb.Attribute(name="followerId", type=S),
        )

        # Posts: a user's posts, newest first via the sort key.
        self.posts_table = self._table("Posts", pk="userId", sk="createdAt")
        self.posts_table.add_global_secondary_index(	# gsi for looking up specific post by post ID
            index_name="byPostId",             
            partition_key=dynamodb.Attribute(name="postId", type=S),
        )

        # Likes: one item per (post, user).
        self.likes_table = self._table("Likes", pk="postId", sk="userId")

        # Comments: a post's comments, oldest first.
        self.comments_table = self._table("Comments", pk="postId", sk="createdAt")

        # Usernames: reserve unique, case-insensitive usernames
        self.usernames_table = self._table("Usernames", pk="usernameLower")

    # Helper function to create a dynamodb table
    def _table(self, name: str, pk: str, sk: str | None = None) -> dynamodb.Table:
        return dynamodb.Table(
            self, name,
            partition_key=dynamodb.Attribute(name=pk, type=S),
            sort_key=dynamodb.Attribute(name=sk, type=S) if sk else None,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,             # cdk destroy deletes table
        )

