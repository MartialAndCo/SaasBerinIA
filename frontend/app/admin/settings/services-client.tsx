"use client";

import { Suspense, useState, useEffect } from "react";
import dynamic from 'next/dynamic';

// Chargement dynamique du composant ServicesTab
const ServicesTab = dynamic(() => import('./components/services-tab'), {
  loading: () => (
    <div className="flex justify-center py-8">
      <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
    </div>
  ),
  ssr: false
});

export default function ServicesClient() {
  return <ServicesTab />;
}
