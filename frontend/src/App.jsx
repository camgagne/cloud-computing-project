import { useState } from "react";
import "./App.css";

function App() {
  const [search, setSearch] = useState("");

  const [posts, setPosts] = useState(
    Array.from({ length: 8 }, (_, i) => ({
      id: i + 1,
      label: `Post ${i + 1}`,
    }))
  );

  function addPost() {
    const id = Math.max(0, ...posts.map(p => p.id)) + 1;

    setPosts(prev => [  
      { id, label: `Post ${id}` },
      ...prev,
    ]);
  }

  const filteredPosts = posts.filter(post =>
    post.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <header>
        <input
          id="search"
          type="search"
          placeholder="Search posts..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        <button id="post-btn" onClick={addPost}>
          Post
        </button>
      </header>

      <main id="posts">
        {filteredPosts.map(post => (
          <div
            key={post.id}
            className="post"
            title={post.label}
          />
        ))}
      </main>
    </>
  );
}

export default App;
