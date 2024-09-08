import "./index.scss";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import MintPage from "./pages/MintPage";
import AppBar from "./components/AppBar";
import PostPage from "./pages/PostPage";

export interface Page {
  name: string;
  component: JSX.Element;
  path: string;
}
function App() {
  const pages: Page[] = [
    {
      name: "Home",
      component: <LandingPage />,
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
          {pages.map((page) => (
            <Route path={page.path} element={page.component} />
          ))}
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
