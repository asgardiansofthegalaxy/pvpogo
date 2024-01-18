import React from "react";
import bckImage from "./assets/sunflower-bg.jpg";

const App: React.FC = () => {
  return (
    <>
      <div
        className="bg-cover bg-center h-screen w-full"
        style={{ backgroundImage: `url(${bckImage})` }}
      >
        <div className="flex flex-col items-center justify-center h-full">
          <h1 className="text-8xl font-bold text-black mb-2">PvPogo</h1>
          <p className="text-4xl text-black mt-8 mb-8">
            A new way of battling in Pokemon go will be here soon
          </p>
          <p className="text-4xl text-black mt-8 mb-8">
            Subscribe to know more information
          </p>
          <input type="email" placeholder="Enter your email" className="p-2" />
        </div>
      </div>
    </>
  );
};

export default App;
