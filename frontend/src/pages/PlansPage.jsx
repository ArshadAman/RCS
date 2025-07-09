import React, { useEffect, useState } from "react";
import { plans } from "../api/api";
import Button from "../components/Button";

export default function PlansPage({ onSelect }) {
  const [planList, setPlanList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    plans
      .list()
      .then((data) => setPlanList(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-10">Loading plans...</div>;
  if (error) return <div className="text-center text-red-500 py-10">{error}</div>;

  return (
    <div className="max-w-2xl mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6 text-center">Choose a Plan</h1>
      <div className="grid md:grid-cols-3 gap-6">
        {planList.map((plan) => (
          <div
            key={plan.id}
            className="bg-white rounded-xl shadow p-6 flex flex-col items-center border border-slate-100"
          >
            <h2 className="font-bold text-xl mb-2 capitalize">{plan.plan_type}</h2>
            <div className="text-3xl font-extrabold mb-2">{plan.review_limit} reviews</div>
            <div className="mb-4 text-slate-500">{plan.company ? plan.company.name : ""}</div>
            <Button
              className="w-full mt-auto bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded"
              onClick={() => onSelect && onSelect(plan)}
            >
              Select
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
