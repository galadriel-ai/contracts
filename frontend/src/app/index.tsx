import "./index.scss";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import MintPage from "./pages/MintPage";
import ProfilePage from "./pages/ProfilePage";
import AppBar from "./components/AppBar";

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
      component: <div>Create</div>,
      path: "/create",
    },
    {
      name: "Mint",
      component: <MintPage />,
      path: "/mint",
    },
    {
      name: "Profile",
      component: <ProfilePage />,
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
