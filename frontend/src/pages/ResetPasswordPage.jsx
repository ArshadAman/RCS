import React from "react";

const ResetPasswordPage = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded shadow text-center">
        <h1 className="text-2xl font-bold mb-6">Reset Password (Demo)</h1>
        <div className="text-gray-600">
          Password reset is disabled in demo mode.
          <br />
          Use <b>admin</b> / <b>admin</b> to login.
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
