import type { Page } from "../..";
import { Link } from "react-router-dom";
import logo from "../../../assets/images/logo.png";
import profile from "../../../assets/icons/profile.svg";
import search from "../../../assets/icons/search.svg";
import "./index.scss";
import { useEffect } from "react";
import { useWeb3Modal } from "@web3modal/ethers/react";
import { useWeb3ModalAccount } from "@web3modal/ethers/react";
import { BrowserProvider } from "ethers";
import { useWeb3ModalProvider } from "@web3modal/ethers/react";
import login from "../../../services/api/loginApi";
import { Eip1193Provider } from "ethers";

export interface AppBarProps {
  pages: Page[];
}

const AppBar: React.FC<AppBarProps> = ({ pages }) => {
  const { open } = useWeb3Modal();
  const { address, isConnected } = useWeb3ModalAccount();
  const { walletProvider } = useWeb3ModalProvider();

  useEffect(() => {
    const backendLogin = async () => {
      if (isConnected) {
        console.log("Connected to wallet");
        const provider = new BrowserProvider(walletProvider as Eip1193Provider);
        const signer = await provider.getSigner();
        const message = "Login";
        const signature = (await signer?.signMessage("Login")) as string;
        const data = login(address as string, message, signature);
        console.log(data);
      }
    };
    backendLogin();
  }, [isConnected]);

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
      <button onClick={() => open()} className="app-bar-wallet-connect">
        {isConnected ? address : "Connect Wallet"}
      </button>
      <img className="app-bar-profile" src={profile} />
    </div>
  );
};

export default AppBar;
