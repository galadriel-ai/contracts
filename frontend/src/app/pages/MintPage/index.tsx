import TextareaAutosize from "react-autosize-textarea";
import "./index.scss";
import { useState } from "react";
import sparkles from "../../../assets/icons/sparkles.svg";

const MintPage: React.FC = () => {
  const [initial, _] = useState(true);
  const [images, __] = useState([
    "https://plus.unsplash.com/premium_photo-1683865776032-07bf70b0add1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dXJsfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1624555130581-1d9cca783bc0?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8dXJsfGVufDB8fDB8fHww",
    "https://plus.unsplash.com/premium_photo-1683865776032-07bf70b0add1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dXJsfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1624555130581-1d9cca783bc0?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8dXJsfGVufDB8fDB8fHww",
    "https://plus.unsplash.com/premium_photo-1683865776032-07bf70b0add1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dXJsfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1624555130581-1d9cca783bc0?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8dXJsfGVufDB8fDB8fHww",
  ]);
  return (
    <div className="mint-page-container">
      <div className="mint-page-banner">
        <div className="mint-page-banner-title">Mint your NFT with AI</div>
        <div className="mint-page-banner-description">
          What exactly do you need? Please describe
        </div>
        <div className="mint-page-banner-chat-container">
          <img src={sparkles} alt="sparkles" />
          <TextareaAutosize
            placeholder={
              initial ? "What's on your mind today?" : "Any changes ?"
            }
            className="mint-page-banner-chat-input"
            onPointerEnterCapture={undefined}
            onPointerLeaveCapture={undefined}
          />
          <button className="mint-page-banner-chat-button">Send</button>
        </div>
      </div>
      <div className="mint-page-image-grid-container">
        {images.map((image) => (
          <div className="mint-page-image-container">
            <img className="mint-page-image" src={image} alt="mintable-image" />
            <button className="mint-page-image-mint-button">Mint</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MintPage;
