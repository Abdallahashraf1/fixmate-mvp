"use client";

import React, { useEffect, useState } from "react";
import { useChat } from "../context/ChatContext";

export default function Controls() {
  const { role, make, model, setRole, setMake, setModel } = useChat();
  const [makes, setMakes] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/meta/makes`)
      .then(r => r.json())
      .then(setMakes);
  }, []);

  useEffect(() => {
    if (!make) return setModels([]);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/meta/models?make=${make}`)
      .then(r => r.json())
      .then(setModels);
  }, [make]);

  return (
    <div className="flex gap-4 p-4">
      <select value={role} onChange={e => setRole(e.target.value as any)}>
        <option>Car Specialist</option>
        <option>Car Owner</option>
      </select>
      <select value={make} onChange={e => setMake(e.target.value)}>
        <option value="">Make</option>
        {makes.map(mk => <option key={mk}>{mk}</option>)}
      </select>
      <select value={model} onChange={e => setModel(e.target.value)}>
        <option value="">Model</option>
        {models.map(md => <option key={md}>{md}</option>)}
      </select>
    </div>
);
}
