import axios from "axios";

console.log(process.env.BACKEND_URL);
export const basicAxios = axios.create({
  baseURL: process.env.BACKEND_URL,
});
