import "./globals.css";

export const metadata = {
  title: "Political Fingerprint",
  description: "Understand how a politician actually behaves in 60 seconds.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
