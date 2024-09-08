import ReactDropdown from "react-dropdown";
import profile from "../../../assets/icons/profile.svg";
import "./index.scss";
import { useState } from "react";

type ContentType = "post" | "nft";

export interface Content {
  id: string;
  value: string; // text in case of post and image url in case of nft
  creater: string;
  type: ContentType;
}

const HomePage: React.FC = () => {
  const posts: Content[] = [
    {
      id: "1",
      value: "Hello World",
      creater: "0x123",
      type: "post",
    },
    {
      id: "2",
      value:
        "https://plus.unsplash.com/premium_photo-1683865776032-07bf70b0add1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dXJsfGVufDB8fDB8fHww",
      creater: "0x123",
      type: "nft",
    },
    {
      id: "1",
      value: "Hello World",
      creater: "0x123",
      type: "post",
    },
    {
      id: "2",
      value:
        "https://plus.unsplash.com/premium_photo-1683865776032-07bf70b0add1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8dXJsfGVufDB8fDB8fHww",
      creater: "0x123",
      type: "nft",
    },
  ];
  const options = ["Ethereum Network", "Sepolia Network", "Goerli Network"];
  const [selected, setSelected] = useState(options[0]);

  return (
    <div className="home-page-container">
      <div className="home-page-content-container">
        <div className="home-page-content-header-container">
          <div className="home-page-content-header-title">Explore</div>
          <div className="home-page-content-header-dropdown-container">
            <ReactDropdown
              className="home-page-content-header-dropdown"
              options={options}
              value={selected}
              onChange={(option) => setSelected(option.value)}
            />
          </div>
        </div>
        <div className="home-page-content-list-container">
          {posts.map((post) =>
            post.type === "post" ? (
              <div className="home-page-content-post-container">
                <div className="home-page-content-post-header">
                  <img src={profile} alt="profile" />
                  <div className="home-page-content-creator">
                    {post.creater}
                  </div>
                </div>
                <div className="home-page-post">{post.value}</div>
              </div>
            ) : (
              <div className="home-page-content-nft-container">
                <div className="home-page-content-nft-header">
                  <img src={profile} alt="profile" />
                  <div className="home-page-content-creator">
                    {post.creater}
                  </div>
                </div>
                <img
                  className="home-page-content-nft-image"
                  src={post.value}
                  alt="nft"
                />
                <div className="home-page-content-nft-footer">
                  <div className="home-page-content-nft-footer-bid-container">
                    <input
                      type="number"
                      placeholder="Enter bid amount"
                      className="home-page-content-nft-footer-bid-amount"
                    />
                    <button className="home-page-content-nft-footer-bid-button">
                      Bid
                    </button>
                  </div>
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
