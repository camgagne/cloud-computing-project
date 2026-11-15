const HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Group 4</title>
  <style>
    :root {
      --bg: #f5f5f5;
      --fg: #111;
      --accent: #1a1a1a;
      --border: #ccc;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--fg);
      min-height: 100vh;
    }

    header {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      background: #fff;
      position: sticky;
      top: 0;
    }

    #search {
      flex: 1;
      min-width: 0;
      padding: 0.65rem 0.85rem;
      font-size: 1rem;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: #fff;
    }

    #post-btn {
      padding: 0.65rem 1.25rem;
      font-size: 1rem;
      font-family: inherit;
      border: none;
      border-radius: 4px;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      white-space: nowrap;
    }

    #post-btn:hover {
      background: #333;
    }

    #posts {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 1rem;
      padding: 1.25rem;
      max-width: 960px;
      margin: 0 auto;
    }

    .post {
      aspect-ratio: 1;
      background: #000;
      border-radius: 2px;
    }

    .post.hidden {
      display: none;
    }
  </style>
</head>
<body>
  <header>
    <input id="search" type="search" placeholder="Search posts..." aria-label="Search posts" />
    <button id="post-btn" type="button">Post</button>
  </header>
  <main id="posts" aria-label="Posts"></main>
  <script>
    const postsEl = document.getElementById("posts");
    const searchEl = document.getElementById("search");
    const postBtn = document.getElementById("post-btn");

    let posts = Array.from({ length: 8 }, (_, i) => ({
      id: i + 1,
      label: "Post " + (i + 1),
    }));

    function render() {
      const query = searchEl.value.trim().toLowerCase();
      postsEl.innerHTML = "";
      posts.forEach((post) => {
        const el = document.createElement("div");
        el.className = "post";
        el.title = post.label;
        el.dataset.label = post.label.toLowerCase();
        if (query && !post.label.toLowerCase().includes(query)) {
          el.classList.add("hidden");
        }
        postsEl.appendChild(el);
      });
    }

    searchEl.addEventListener("input", render);

    postBtn.addEventListener("click", () => {
      const id = posts.length + 1;
      posts = [{ id, label: "Post " + id }, ...posts];
      render();
    });

    render();
  </script>
</body>
</html>`;

exports.handler = async () => {
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
    },
    body: HTML,
  };
};
