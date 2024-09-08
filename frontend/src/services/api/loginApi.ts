import axios from "axios";
const login = async (
  address: string,
  message: string,
  signedMessage: string
) => {
  const data = axios.post(
    `https://9261-2401-4900-8838-6e3d-1b70-8d1e-a8bd-8b4d.ngrok-free.app/api/v1/auth/login/`,
    {
      address: address,
      message: message,
      signature: signedMessage,
    }
  );
  return data;
};

export default login;
