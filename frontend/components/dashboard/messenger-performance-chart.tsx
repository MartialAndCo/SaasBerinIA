import React from 'react';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MessengerPerformanceChartProps {
  data: {
    labels: string[];
    emailOpenRates: number[];
    smsDeliveryRates: number[];
    conversionRates: number[];
  };
}

export const MessengerPerformanceChart: React.FC<MessengerPerformanceChartProps> = ({ data }) => {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Email Open Rates',
        data: data.emailOpenRates,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        type: 'line',
      },
      {
        label: 'SMS Delivery Rates',
        data: data.smsDeliveryRates,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        type: 'bar',
      },
      {
        label: 'Conversion Rates',
        data: data.conversionRates,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        type: 'line',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Messenger Performance Overview',
      },
    },
  };

  return <Bar data={chartData as any} options={options} />;
};
