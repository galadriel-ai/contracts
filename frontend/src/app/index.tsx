import "./index.scss";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { createWeb3Modal, useWeb3ModalAccount } from "@web3modal/ethers/react";
import { ethersConfig, galadriel, projectId } from "../services/auth";

// import LandingPage from "./pages/LandingPage";
import HomePage from "./pages/HomePage";
import MintPage from "./pages/MintPage";
import AppBar from "./components/AppBar";
import PostPage from "./pages/PostPage";
import LandingPage from "./pages/LandingPage";
// import { useEffect } from "react";

export interface Page {
  name: string;
  component: JSX.Element;
  path: string;
}

createWeb3Modal({
  ethersConfig,
  chains: [galadriel],
  projectId,
});

const App: React.FC = () => {
  const { isConnected } = useWeb3ModalAccount();
  const pages: Page[] = [
    {
      name: "Home",
      component: <HomePage />,
      path: "/",
    },
    {
      name: "Create",
      component: <PostPage />,
      path: "/post",
    },
    {
      name: "Mint",
      component: <MintPage />,
      path: "/mint",
    },
    {
      name: "Profile",
      component: <div>Profile</div>,
      path: "/profile",
    },
  ];

  return (
    <BrowserRouter>
      <div className="app-container">
        <AppBar pages={pages} />
        <Routes>
          {isConnected ? (
            pages.map((page) => (
              <Route path={page.path} element={page.component} />
            ))
          ) : (
            <Route path="*" element={<LandingPage />} />
          )}
        </Routes>
      </div>
    </BrowserRouter>
  );
};

export default App;
