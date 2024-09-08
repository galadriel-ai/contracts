import React from "react";
import banner from "../../../assets/gif/banner.gif";
import sparkles from "../../../assets/icons/sparkles.svg";
import "./index.scss";

const LandingPage: React.FC = () => {
  return (
    <div className="landing-page-container">
      <div className="landing-page-banner">
        <img className="landing-page-banner-icon" src={banner} alt="banner" />
        <div>
          <div className="landing-page-banner-title">Empowering Creators</div>
          <div className="landing-page-banner-title">Respecting Ownership</div>
        </div>
        <div className="landing-page-banner-description">
          Our platform is designed to foster a community where artists can share
          their work, inspire others, and be fairly compensated for their
          contributions
        </div>
        <button className="landing-page-banner-chat-button">
          <img
            className="landing-page-banner-chat-icon"
            src={sparkles}
            alt="sparkles"
          />
          <p className="landing-page-banner-chat-content">Chat Now</p>
        </button>
      </div>
    </div>
  );
};

export default LandingPage;
