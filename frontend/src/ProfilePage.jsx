import { useEffect, useState } from "react";
import { fetchAuthSession, getCurrentUser } from "aws-amplify/auth";

export default function ProfilePage({ onBack }) {
    // state for user, posts, error
    const [user, setUser] = useState(null);
    const [posts, setPosts] = useState([]);
    const [error, setError] = useState("");

    useEffect(() => {
        async function load() {
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

                // fetch the user and their posts, then set state

                // Get the current user's ID from the Cognito session
                const { userId } = await getCurrentUser();

                // Fetch the user's profile information
                const userResponse = await fetch(
                    `${config.apiUrl}/users/${userId}`,
                    {
                        "Authorization": `Bearer ${token}`,
                        method: "GET",
                        headers: {
                            "Authorization": token,
                        },
                    }
                );
                // Check if the response is OK
                if (!userResponse.ok) {
                    throw new Error("Failed to fetch user profile");
                }
                
                const userData = await userResponse.json();

                // Fetch the user's posts
                const postsResponse = await fetch(
                    `${config.apiUrl}/users/${userId}/posts`,
                    {
                        "Authorization": `Bearer ${token}`,
                        method: "GET",
                        headers: {
                            "Authorization": token,
                        },
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
    }, []);

        return (
        <div>
            {/* show error if there is one */}
            {error && <p className="error">Error: {error}</p>}
            {user == null ? (<p>Loading user info...</p>) :
            (
                <div>
                    {/* no username yet, use email in meantime
                    <h2>Username:{user.username}</h2> */}
                    <h2>Username: {user.email}</h2>
                    <p>Followers: {user.followerCount}</p>
                    <p>Following: {user.followingCount}</p>
                </div>
            )}
            
            {posts.length == 0 ? (<p>No posts found.</p>) :
            (
                <div className="profile-posts">
                    {posts.map(post => (
                        <div key={post.postId} className="profile-post">
                            {/* Display image, caption, date */}
                            <img src={post.imageUrl} width="500" />
                            <p>{post.caption}</p>
                            <p>{new Date(post.createdAt).toLocaleString()}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}