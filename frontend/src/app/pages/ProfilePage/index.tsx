import TextareaAutosize from "react-autosize-textarea";
import "./index.scss";

const ProfilePage: React.FC = () => {
  return (
    <div className="profile-page-container">
      <div className="profile-page-header">
        <div className="profile-page-header-title">Create Post</div>
        <div className="profile-page-header-description">
          Once your item is minted you will not be able to change any of its
          information.
        </div>
      </div>
      <div className="profile-page-post-container">
        <TextareaAutosize
          placeholder="What's on your mind today?"
          className="profile-page-post-input"
          onPointerEnterCapture={undefined}
          onPointerLeaveCapture={undefined}
        />
        <button className="profile-page-post-button">Send</button>
      </div>
    </div>
  );
};

export default ProfilePage;
