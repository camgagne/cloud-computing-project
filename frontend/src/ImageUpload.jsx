import { useState } from "react";

// Retrieve authentication tokens from our existing Cognito session
import { fetchAuthSession } from "aws-amplify/auth";

export default function ImageUpload() {

    // Store the image selected by the user
    const [file, setFile] = useState(null);

    // Store messages shown to the user
    const [status, setStatus] = useState("");

    // Track whether an upload is currently taking place
    const [busy, setBusy] = useState(false);

    // The caption typed by the user
    const [caption, setCaption] = useState("");

    // The saved post, shown after posting
    const [posted, setPosted] = useState(null);

    async function handleUpload() {

        // Do nothing if the user hasn't selected an image
        if (!file) return;

        try {
            // Disable uploading while an upload is in progress
            setBusy(true);
            setStatus("Uploading...");

            // Retrieve config.json containing our API Gateway URL
            const config = await fetch("/config.json")
                .then(res => res.json());

            // Make sure API Gateway has been configured
            if (!config.apiUrl || config.apiUrl === "None") {
                throw new Error("Upload API is not configured");
            }

            // Retrieve the existing Cognito authentication session
            const session = await fetchAuthSession();

            // Extract the user's access token from the session
            const token = session.tokens?.accessToken?.toString();

            // Make sure the user is authenticated
            if (!token) {
                throw new Error("You must be signed in");
            }

            // Send a request to API Gateway asking for
            // a temporary S3 upload URL
            const response = await fetch(
                `${config.apiUrl}/upload`,
                {
                    method: "POST",

                    headers: {
                        // Used by API Gateway to authenticate the user
                        Authorization: `Bearer ${token}`,

                        // We are sending JSON data
                        "Content-Type": "application/json"
                    },

                    // Tell Lambda what kind of image we want to upload
                    body: JSON.stringify({
                        contentType: file.type
                    })
                }
            );

            // Check whether our API request succeeded
            if (!response.ok) {
                throw new Error("Failed to get upload URL");
            }

            // Extract the temporary URL and S3 object key
            // returned by our Lambda function
            const { uploadUrl, imageKey } = await response.json();

            // Upload the actual image directly to S3
            const upload = await fetch(uploadUrl, {
                method: "PUT",

                headers: {
                    "Content-Type": file.type
                },

                // The actual image file
                body: file
            });

            // Check whether S3 successfully stored the image
            if (!upload.ok) {
                throw new Error("Image upload failed");
            }

            // Save the post (imageKey + caption) in DynamoDB
            const postResponse = await fetch(
                `${config.apiUrl}/posts`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ imageKey, caption })
                }
            );

            // Check whether the post was saved
            if (!postResponse.ok) {
                throw new Error("Failed to save post");
            }

            // Keep the saved post plus a local preview of the image
            const post = await postResponse.json();
            setPosted({ ...post, preview: URL.createObjectURL(file) });

            // Notify the user that the upload succeeded
            setStatus("Image uploaded successfully!");

            // Print the S3 object key for debugging
            // Eventually this can be stored in DynamoDB
            console.log(imageKey);

        } catch (error) {

            // Display an error if anything goes wrong
            setStatus(error.message);

        } finally {

            // Re-enable the upload button regardless of
            // whether the upload succeeded or failed
            setBusy(false);
        }
    }


    return (
        <div>

            {/* Allow the user to select an image from their computer */}
            <input
                type="file"

                // Suggested file types in the browser's file picker
                accept="image/jpeg,image/png,image/webp"

                // Disable file selection during an upload
                disabled={busy}

                // Store the selected file in our React state
                onChange={e => setFile(e.target.files[0])}
            />

            {/* Caption field */}
            <input
                placeholder="Caption"
                value={caption}
                disabled={busy}
                onChange={e => setCaption(e.target.value)}
            />

            {/* Execute handleUpload when the button is clicked */}
            <button
                onClick={handleUpload}

                // Disable if no file is selected or we're uploading
                disabled={!file || busy}
            >
                {busy ? "Uploading..." : "Post"}
            </button>

            {/* Display success or error messages */}
            <p>{status}</p>


            {/* Show the image and caption that were just posted */}
            {posted && (
                <div>
                    <img src={posted.preview} width="300" />
                    <p>{posted.caption}</p>
                </div>
            )}

        </div>
    );
}