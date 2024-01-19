// Make sure to run npm install @formspree/react
// For more help visit https://formspr.ee/react-help

import { useForm, ValidationError } from "@formspree/react";

function ContactForm() {
  const [state, handleSubmit] = useForm("mayrngon");
  if (state.succeeded) {
    return (
      <p className="text-lg md:text-xl font-semibold text-white mt-4 mb-6 p-4 bg-blue-500 rounded-lg shadow-md">
        🎉 You're all set! Welcome to the community. Check your inbox for
        exciting updates and exclusive content coming your way!
      </p>
    );
  }
  return (
    <form onSubmit={handleSubmit} className="flex flex-col items-center my-6">
      <input
        id="email"
        type="email"
        name="email"
        className="px-4 py-2 mb-8 w-64 border rounded-full"
        placeholder="Enter your email"
        required
      />
      <ValidationError prefix="Email" field="email" errors={state.errors} />
      <button
        type="submit"
        disabled={state.submitting}
        className="px-6 py-2 border rounded bg-blue-500 text-white hover:bg-blue-600"
      >
        Subscribe
      </button>
    </form>
  );
}

export default ContactForm;
