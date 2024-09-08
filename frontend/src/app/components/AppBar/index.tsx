import type { Page } from "../..";
import { Link } from "react-router-dom";
import logo from "../../../assets/images/logo.png";
import profile from "../../../assets/icons/profile.svg";
import search from "../../../assets/icons/search.svg";
import "./index.scss";

export interface AppBarProps {
  pages: Page[];
}

const AppBar: React.FC<AppBarProps> = ({ pages }) => {
  return (
    <div className="app-bar">
      <Link className="app-bar-logo" to="/">
        <img src={logo} alt="logo" height={50} />
      </Link>
      {pages.map((page) => (
        <Link className="app-bar-page-links" to={page.path}>
          {page.name}
        </Link>
      ))}
      <div className="app-bar-search-container">
        <img className="app-bar-search-icon" src={search} alt="search" />
        <input
          className="app-bar-search"
          type="text"
          placeholder="Search posts or people"
        />
      </div>
      <button className="app-bar-wallet-connect">Connect Wallet</button>
      <img className="app-bar-profile" src={profile} />
    </div>
  );
};

export default AppBar;
