import React, { useState } from "react";
import { auth, businesses, plans } from "../api/api";
import PlansPage from "./PlansPage";
import Button from "../components/Button";

export default function BusinessRegisterPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({});
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan);
    setStep(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // 1. Register user
      const user = await auth.register({
        username: form.email,
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
      });
      // 2. Create company
      // (Assume backend auto-creates company for user, or add company creation here)
      // 3. Create business
      await businesses.create({
        name: form.business_name,
        company: user.company_id, // or get from user profile
        category: form.category,
        address: form.address,
        phone_number: form.phone_number,
        email: form.email,
        website: form.website,
      });
      // 4. Assign plan (if needed)
      // ...
      setSuccess(true);
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  if (success)
    return (
      <div className="max-w-md mx-auto py-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Registration Successful!</h1>
        <p className="mb-6">You can now log in and start collecting reviews.</p>
        <Button onClick={() => (window.location.href = "/login")}>Go to Login</Button>
      </div>
    );

  if (step === 1)
    return <PlansPage onSelect={handlePlanSelect} />;

  return (
    <div className="max-w-md mx-auto py-10">
      <h1 className="text-2xl font-bold mb-6 text-center">Register Your Business</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          name="first_name"
          placeholder="First Name"
          className="w-full border p-2 rounded"
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="last_name"
          placeholder="Last Name"
          className="w-full border p-2 rounded"
          onChange={handleChange}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Email"
          className="w-full border p-2 rounded"
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          className="w-full border p-2 rounded"
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="business_name"
          placeholder="Business Name"
          className="w-full border p-2 rounded"
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="category"
          placeholder="Category"
          className="w-full border p-2 rounded"
          onChange={handleChange}
        />
        <input
          type="text"
          name="address"
          placeholder="Address"
          className="w-full border p-2 rounded"
          onChange={handleChange}
        />
        <input
          type="text"
          name="phone_number"
          placeholder="Phone Number"
          className="w-full border p-2 rounded"
          onChange={handleChange}
        />
        <input
          type="text"
          name="website"
          placeholder="Website"
          className="w-full border p-2 rounded"
          onChange={handleChange}
        />
        {error && <div className="text-red-500 text-sm">{error}</div>}
        <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded" disabled={loading}>
          {loading ? "Registering..." : "Register"}
        </Button>
      </form>
    </div>
  );
}
