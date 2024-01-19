import ContactForm from "./ContactForm";
import bckImage from "./assets/sunflower-bg.jpg";

function App() {
  return (
    <div
      className="h-screen bg-cover bg-no-repeat bg-center"
      style={{ backgroundImage: `url(${bckImage})` }}
    >
      <div className="flex flex-col items-center justify-center h-full text-center bg-opacity-50 bg-gray-700 px-4">
        <h1 className="text-6xl md:text-8xl lg:text-12xl font-bold text-teal-950 mb-4 my-6">
          PvPogo
        </h1>
        <p className="text-lg font-bold text-teal-950 md:text-3xl mb-6 mx-4 my-12">
          A new way to learn Pokemon PvP will be here soon. Get excited!
        </p>
        <ContactForm />
      </div>
    </div>
  );
}

export default App;
