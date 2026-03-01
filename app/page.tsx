"use client";

import { Button, Input, Card, CardBody, CardHeader } from "@heroui/react";
import { useForm, ValidationError } from "@formspree/react";
import { useState } from "react";
import Link from "next/link";

function ContactForm() {
  const [state, handleSubmit] = useForm("mayrngon");
  const [email, setEmail] = useState("");

  if (state.succeeded) {
    return (
      <Card className="w-full max-w-md mt-6">
        <CardBody className="text-center py-8">
          <p className="text-lg font-semibold text-success">
            You&apos;re all set! Welcome to the community. Check your inbox for
            exciting updates and exclusive content coming your way!
          </p>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="flex-col items-start">
        <p className="text-md">Subscribe to our newsletter</p>
        <p className="text-small text-default-500">Get the latest updates</p>
      </CardHeader>
      <CardBody>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            id="email"
            type="email"
            name="email"
            placeholder="Enter your email"
            value={email}
            onValueChange={setEmail}
            isRequired
          />
          <ValidationError prefix="Email" field="email" errors={state.errors} />
          <Button
            type="submit"
            color="primary"
            isLoading={state.submitting}
            className="w-full"
          >
            Subscribe
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

export default function Home() {
  return (
    <main
      className="min-h-screen bg-cover bg-no-repeat bg-center flex flex-col items-center justify-center text-center px-4"
      style={{
        backgroundImage: `url(/sunflower-bg.jpg)`,
      }}
    >
      <div className="bg-gray-700/50 w-full min-h-screen flex flex-col items-center justify-center py-12 px-4">
        <h1 className="text-6xl md:text-8xl font-bold text-teal-950 mb-4">
          PvPogo
        </h1>
        <p className="text-lg font-bold text-teal-950 md:text-3xl mb-6 max-w-2xl">
          Unleash Your Pokémon Mastery: The Ultimate PvP Learning Adventure
          Awaits!
        </p>
        <div className="flex gap-4 mb-6">
          <Link href="/team">
            <Button size="lg" color="primary" className="font-bold">
              Build Your Team
            </Button>
          </Link>
        </div>
        <ContactForm />
      </div>
    </main>
  );
}
