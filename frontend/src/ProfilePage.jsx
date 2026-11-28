import { useEffect, useState } from "react";
import { fetchAuthSession, getCurrentUser } from "aws-amplify/auth";
import "./ProfilePage.css";

export default function ProfilePage({ userId }) {
    // state for user, posts, error
    const [user, setUser] = useState(null);
    const [posts, setPosts] = useState([]);
    const [error, setError] = useState("");
    const [followBusy, setFollowBusy] = useState(false);

    useEffect(() => {
        async function load() {
            setUser(null);
            setPosts([]);
            setError("");
            try {
                // Retrieve config.json containing our API Gateway URL
                const config = await fetch("/config.json")
                    .then(res => res.json());

                // Make sure API Gateway has been configured
                if (!config.apiUrl || config.apiUrl === "None") {
                    throw new Error("API is not configured");
                }

                // Retrieve the existing Cognito authentication session
                const session = await fetchAuthSession();

                // Extract the user's access token from the session
                const token = session.tokens?.accessToken?.toString();

                // Make sure the user is authenticated
                if (!token) {
                    throw new Error("You must be signed in");
                }

                // Get the currently authenticated user
                const currentUser = await getCurrentUser();

                // Use the selected user's ID, otherwise use our own ID
                const profileUserId = userId ?? currentUser.userId;

                // Fetch the user's profile information
                const userResponse = await fetch(
                    `${config.apiUrl}/users/${profileUserId}`,
                    {
                        method: "GET",
                        headers: {
                        Authorization: `Bearer ${token}`
                        }
                    }
                );
                // Check if the response is OK
                if (!userResponse.ok) {
                    throw new Error("Failed to fetch user profile");
                }

                const userData = await userResponse.json();

                // Fetch the user's posts
                const postsResponse = await fetch(
                    `${config.apiUrl}/users/${profileUserId}/posts`,
                    {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    }
                );

                if (!postsResponse.ok) {
                    throw new Error("Failed to fetch user posts");
                }

                const postsData = await postsResponse.json();
                setPosts(postsData);
                setUser(userData);

            } catch (err) {
                // show the error
                setError(err.message);
            }
        }
        load();
    }, [userId]);

    async function toggleFollow() {
        if (!user || user.isSelf || followBusy) return;

        setFollowBusy(true);
        setError("");
        try {
            const config = await fetch("/config.json").then((res) => res.json());
            const session = await fetchAuthSession();
            const token = session.tokens?.accessToken?.toString();
            if (!token) {
                throw new Error("You must be signed in");
            }

            const action = user.isFollowing ? "unfollow" : "follow";
            const response = await fetch(
                `${config.apiUrl}/users/${user.userId}/${action}`,
                {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            if (!response.ok) {
                throw new Error(`Failed to ${action} user`);
            }

            const data = await response.json();
            setUser((prev) => ({
                ...prev,
                isFollowing: data.following,
                followerCount: data.following
                    ? Number(prev.followerCount) + 1
                    : Math.max(0, Number(prev.followerCount) - 1),
            }));
        } catch (err) {
            setError(err.message);
        } finally {
            setFollowBusy(false);
        }
    }

    return (
        <div className="profile-container">

            {/* Profile sidebar */}
            <aside className="profile-sidebar">

                {user == null ? (
                    <p>Loading user info...</p>
                ) : (
                    <>
                    <div className="profile-avatar">
                        {user.username?.charAt(0).toUpperCase()}
                    </div>

                    <h2 className="profile-email">
                        {user.username}
                    </h2>

                    <p className="profile-subtitle">
                        Community member
                    </p>

                    {!user.isSelf && (
                        <button
                            type="button"
                            className={`follow-btn ${user.isFollowing ? "following" : ""}`}
                            onClick={toggleFollow}
                            disabled={followBusy}
                        >
                            {followBusy
                                ? "Saving…"
                                : user.isFollowing
                                    ? "Following"
                                    : "Follow"}
                        </button>
                    )}

                    <div className="profile-stats">

                        <div className="profile-stat">
                            <span>Posts</span>
                            <strong>{posts.length}</strong>
                        </div>

                        <div className="profile-stat">
                            <span>Followers</span>
                            <strong>{user.followerCount}</strong>
                        </div>

                        <div className="profile-stat">
                            <span>Following</span>
                            <strong>{user.followingCount}</strong>
                        </div>

                    </div>

                    <div className="profile-navigation">
                        <span className="profile-nav-active">
                            Posts
                        </span>
                    </div>
                </>
            )}

        </aside>

        {/* Main content */}
        <main className="profile-content">

            <div className="profile-content-header">
                <h2>Recent activity</h2>
                <span>{posts.length} posts</span>
            </div>

            {error && <p className="error">Error: {error}</p>}

            {posts.length === 0 ? (
                <p className="no-posts">No posts found.</p>
            ) : (
                <div className="profile-posts">

                    {posts.map(post => (
                        <div key={post.postId} className="profile-post">

                            <img
                                src={post.imageUrl}
                                alt="User post"
                                loading="lazy"
                            />

                            <div className="profile-post-content">

                                <p className="profile-post-caption">
                                    {post.caption}
                                </p>

                                <p className="profile-post-date">
                                    {new Date(post.createdAt).toLocaleString()}
                                </p>

                            </div>
                        </div>
                    ))}

                </div>
            )}

        </main>

    </div>
    );
}
