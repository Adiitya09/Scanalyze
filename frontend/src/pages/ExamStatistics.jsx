import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  ChartBarIcon,
  UserGroupIcon,
  TrophyIcon,
  BookOpenIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { examAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';

const ExamStatistics = () => {
  const { examId } = useParams();
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const response = await examAPI.exportCSV(examId);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `exam_${examId}_results.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Results exported to CSV successfully! 📥');
    } catch (error) {
      console.error('Failed to export CSV:', error);
      toast.error('Failed to export CSV results');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
  }, [examId]);

  const fetchStatistics = async () => {
    try {
      const response = await examAPI.getStatistics(examId);
      setStatistics(response.data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
      toast.error('Failed to load exam statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading statistics..." />;
  }

  if (!statistics) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No statistics available</h3>
        <p className="mt-1 text-sm text-gray-500">
          No student submissions found for this exam.
        </p>
        <div className="mt-6">
          <Link
            to="/teacher/dashboard"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const questionAccuracyData = Object.entries(statistics.question_wise_accuracy).map(([question, accuracy]) => ({
    question: `Q${question}`,
    accuracy: parseFloat(accuracy),
    difficulty: accuracy > 75 ? 'Easy' : accuracy > 50 ? 'Medium' : 'Hard'
  }));

  const scoreDistributionData = [
    { range: '90-100%', count: 0, color: '#10b981' },
    { range: '80-89%', count: 0, color: '#3b82f6' },
    { range: '70-79%', count: 0, color: '#8b5cf6' },
    { range: '60-69%', count: 0, color: '#f59e0b' },
    { range: '50-59%', count: 0, color: '#ef4444' },
    { range: '0-49%', count: 0, color: '#6b7280' }
  ];

  // This would need actual score data from the API to populate properly
  const passFailData = [
    { name: 'Pass', value: Math.round((statistics.pass_rate / 100) * statistics.total_students), color: '#10b981' },
    { name: 'Fail', value: statistics.total_students - Math.round((statistics.pass_rate / 100) * statistics.total_students), color: '#ef4444' }
  ];

  const topQuestions = questionAccuracyData
    .sort((a, b) => b.accuracy - a.accuracy)
    .slice(0, 5);

  const hardestQuestions = questionAccuracyData
    .sort((a, b) => a.accuracy - b.accuracy)
    .slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Exam Statistics</h1>
              <p className="mt-2 text-gray-600">{statistics.exam_title}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleExportCSV}
              disabled={exporting}
              className="inline-flex items-center px-4 py-2 border border-primary-600 rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              {exporting ? 'Exporting...' : 'Export Results (CSV)'}
            </button>
            <Link
              to="/teacher/dashboard"
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UserGroupIcon className="h-8 w-8 text-blue-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Students
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {statistics.total_students}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrophyIcon className="h-8 w-8 text-green-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Score
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {statistics.average_score}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ArrowUpIcon className="h-8 w-8 text-purple-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Highest Score
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {statistics.highest_score}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-2 rounded-md ${statistics.pass_rate >= 70 ? 'bg-green-500' : 'bg-red-500'}`}>
                  <BookOpenIcon className="h-4 w-4 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Pass Rate
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {statistics.pass_rate.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Question-wise Accuracy */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Question-wise Accuracy</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={questionAccuracyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="question" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Accuracy']} />
                <Bar dataKey="accuracy">
                  {questionAccuracyData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.accuracy >= 75 ? '#10b981' : entry.accuracy >= 50 ? '#f59e0b' : '#ef4444'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pass/Fail Distribution */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Pass/Fail Distribution</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={passFailData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                >
                  {passFailData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Analysis Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Performing Questions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Top Performing Questions
            </h3>
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Question
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Accuracy
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Difficulty
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {topQuestions.map((question, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {question.question}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-3">
                            <div 
                              className="bg-green-500 h-2 rounded-full" 
                              style={{ width: `${question.accuracy}%` }}
                            ></div>
                          </div>
                          <span>{question.accuracy.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          question.difficulty === 'Easy' 
                            ? 'bg-green-100 text-green-800'
                            : question.difficulty === 'Medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {question.difficulty}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Hardest Questions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Most Challenging Questions
            </h3>
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Question
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Accuracy
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Difficulty
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {hardestQuestions.map((question, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {question.question}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-3">
                            <div 
                              className="bg-red-500 h-2 rounded-full" 
                              style={{ width: `${question.accuracy}%` }}
                            ></div>
                          </div>
                          <span>{question.accuracy.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          question.difficulty === 'Easy' 
                            ? 'bg-green-100 text-green-800'
                            : question.difficulty === 'Medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {question.difficulty}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Insights */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-6">
        <div className="flex">
          <ChartBarIcon className="h-5 w-5 text-blue-400 flex-shrink-0" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Exam Analysis Summary</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="space-y-1">
                <li>• {statistics.total_students} students attempted this exam</li>
                <li>• Average performance: {statistics.average_score} marks ({statistics.highest_score > 0 ? ((statistics.average_score / statistics.highest_score) * 100).toFixed(1) : 0}%)</li>
                <li>• Pass rate: {statistics.pass_rate.toFixed(1)}% ({Math.round((statistics.pass_rate / 100) * statistics.total_students)} students passed)</li>
                <li>• Score range: {statistics.lowest_score} - {statistics.highest_score} marks</li>
                <li>• Most challenging areas: Questions with accuracy below 50% need review</li>
                <li>• Well-understood topics: Questions with accuracy above 75% indicate good comprehension</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExamStatistics;