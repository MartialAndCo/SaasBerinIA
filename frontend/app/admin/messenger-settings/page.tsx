"use client"

import React from 'react';
import MessengerServicesConfig from '@/components/dashboard/messenger-services-config';

export default function MessengerSettingsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Paramètres de Messagerie</h1>
      <MessengerServicesConfig />
    </div>
  );
}
