import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-surface border-t border-gray-200 text-text-light py-6 text-center mt-12">
      <span>&copy; {new Date().getFullYear()} ReviewHub. All rights reserved.</span>
    </footer>
  );
}
