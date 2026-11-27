import { useState, useEffect } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import "./UserSearch.css";

export default function UserSearch({ onSelectUser }) {

    const [search, setSearch] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {

        setResults([]);
        setError("");

        // Don't search until the user enters something
        if (!search.trim()) {
            setLoading(false);
            return;
        }

        const controller = new AbortController();

        setLoading(true);

        async function searchUsers() {

            try {
                const config = await fetch("/config.json")
                    .then(res => res.json());

                const session = await fetchAuthSession();

                const token = session.tokens?.accessToken?.toString();

                if (!token) {
                    throw new Error("You must be signed in");
                }

                const response = await fetch(
                    `${config.apiUrl}/users/search?q=${encodeURIComponent(search)}`,
                    {
                        method: "GET",

                        headers: {
                            Authorization: `Bearer ${token}`
                        },

                        signal: controller.signal
                    }
                );

                if (!response.ok) {
                    throw new Error("Failed to search users");
                }

                const users = await response.json();

                if (!controller.signal.aborted) {
                    setResults(users);
                }

            } catch (error) {

                if (!controller.signal.aborted) {
                    setError(error.message);
                }

            } finally {

                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            }
        }

        // Wait until the user stops typing for 300ms
        const timeout = setTimeout(searchUsers, 300);

        return () => {
            clearTimeout(timeout);
            controller.abort();
        };

    }, [search]);

    return (
        <div className="user-search">

            <input
                className="user-search-input"
                type="search"
                placeholder="Search users..."
                aria-label="Search users"
                value={search}
                onChange={e => setSearch(e.target.value)}
            />

            {search.trim() && (
                <div className="search-results">

                    {loading && <p>Searching...</p>}

                    {error && <p>{error}</p>}

                    {!loading && !error && results.length === 0 && (
                        <p>No users found.</p>
                    )}

                    {results.map(user => (
                        <button
                            key={user.userId}
                            className="search-result"
                            onClick={() => {
                                onSelectUser(user.userId);
                                setSearch("");
                            }}
                        >
                            <div className="search-avatar">
                                {user.username.charAt(0).toUpperCase()}
                            </div>

                            <span>{user.username}</span>

                        </button>
                    ))}

                </div>
            )}

        </div>
    );
}