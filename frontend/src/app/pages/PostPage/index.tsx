import TextareaAutosize from "react-autosize-textarea";
import "./index.scss";

const PostPage: React.FC = () => {
  return (
    <div className="post-page-container">
      <div className="post-page-header">
        <div className="post-page-header-title">Create Post</div>
        <div className="post-page-header-description">
          Once your item is minted you will not be able to change any of its
          information.
        </div>
      </div>
      <div className="post-page-post-container">
        <TextareaAutosize
          placeholder="What's on your mind today?"
          className="post-page-post-input"
          onPointerEnterCapture={undefined}
          onPointerLeaveCapture={undefined}
        />
        <button className="post-page-post-button">Send</button>
      </div>
    </div>
  );
};

export default PostPage;
