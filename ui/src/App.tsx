import Evidence from "./components/Evidence";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import HowItWorks from "./components/HowItWorks";
import Nav from "./components/Nav";

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Evidence />
        <HowItWorks />
      </main>
      <Footer />
    </>
  );
}
