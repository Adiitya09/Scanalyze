import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  CheckCircleIcon,
  XCircleIcon,
  MinusCircleIcon,
  TrophyIcon,
  ChartBarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { resultsAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';

const ViewResult = () => {
  const { examId, rollNumber } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResult();
  }, [examId, rollNumber]);

  const fetchResult = async () => {
    try {
      const response = await resultsAPI.getResult(examId, rollNumber);
      setResult(response.data);
    } catch (error) {
      console.error('Failed to fetch result:', error);
      toast.error('Failed to load result');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading results..." />;
  }

  if (!result) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Result not found</h3>
        <p className="mt-1 text-sm text-gray-500">
          No results found for this exam and roll number combination.
        </p>
        <div className="mt-6">
          <Link
            to="/student/dashboard"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Data for pie chart
  const pieData = [
    { name: 'Correct', value: result.correct_answers, color: '#10b981' },
    { name: 'Wrong', value: result.wrong_answers, color: '#ef4444' },
    { name: 'Unanswered', value: result.unanswered, color: '#6b7280' },
  ];

  // Data for bar chart (question-wise performance)
  const questionData = result.answer_breakdown.map((item, index) => ({
    question: `Q${item.question}`,
    status: item.status === 'correct' ? 1 : item.status === 'incorrect' ? -1 : 0,
    correct: item.status === 'correct' ? 1 : 0,
    incorrect: item.status === 'incorrect' ? 1 : 0,
    unanswered: item.status === 'unanswered' ? 1 : 0,
  }));

  const getGradeColor = (percentage) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 75) return 'text-blue-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getGrade = (percentage) => {
    if (percentage >= 90) return 'A+';
    if (percentage >= 85) return 'A';
    if (percentage >= 75) return 'B+';
    if (percentage >= 70) return 'B';
    if (percentage >= 60) return 'C+';
    if (percentage >= 50) return 'C';
    if (percentage >= 40) return 'D';
    return 'F';
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{`${label}`}</p>
          <p className="text-sm text-gray-600">
            Status: {payload[0].payload.correct ? 'Correct' : 
                     payload[0].payload.incorrect ? 'Incorrect' : 'Unanswered'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center">
          <TrophyIcon className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Exam Results</h1>
            <p className="mt-2 text-gray-600">{result.exam_title}</p>
          </div>
        </div>
      </div>

      {/* Score Summary */}
      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className={`text-4xl font-bold ${getGradeColor(result.percentage)}`}>
              {result.score}/{result.max_marks}
            </div>
            <p className="text-sm text-gray-500 mt-1">Total Score</p>
          </div>
          
          <div className="text-center">
            <div className={`text-4xl font-bold ${getGradeColor(result.percentage)}`}>
              {result.percentage.toFixed(1)}%
            </div>
            <p className="text-sm text-gray-500 mt-1">Percentage</p>
          </div>
          
          <div className="text-center">
            <div className={`text-4xl font-bold ${getGradeColor(result.percentage)}`}>
              {getGrade(result.percentage)}
            </div>
            <p className="text-sm text-gray-500 mt-1">Grade</p>
          </div>

          <div className="text-center">
            <div className={`text-4xl font-bold ${result.percentage >= 50 ? 'text-green-600' : 'text-red-600'}`}>
              {result.percentage >= 50 ? 'PASS' : 'FAIL'}
            </div>
            <p className="text-sm text-gray-500 mt-1">Result</p>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div className="flex items-center justify-center">
              <CheckCircleIcon className="h-8 w-8 text-green-500 mr-2" />
              <div>
                <p className="text-2xl font-bold text-green-600">{result.correct_answers}</p>
                <p className="text-sm text-gray-500">Correct</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center">
              <XCircleIcon className="h-8 w-8 text-red-500 mr-2" />
              <div>
                <p className="text-2xl font-bold text-red-600">{result.wrong_answers}</p>
                <p className="text-sm text-gray-500">Wrong</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center">
              <MinusCircleIcon className="h-8 w-8 text-gray-500 mr-2" />
              <div>
                <p className="text-2xl font-bold text-gray-600">{result.unanswered}</p>
                <p className="text-sm text-gray-500">Unanswered</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Pie Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Overview</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Question-wise Performance</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={questionData.slice(0, 20)}> {/* Show first 20 questions */}
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="question" 
                  tick={{ fontSize: 12 }}
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis domain={[-1, 1]} ticks={[-1, 0, 1]} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="status">
                  {questionData.slice(0, 20).map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.status === 1 ? '#10b981' : entry.status === -1 ? '#ef4444' : '#6b7280'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Answer Breakdown */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Detailed Answer Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Your Answer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Correct Answer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {result.answer_breakdown.map((item, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.question}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        item.student_answer === 'Not Answered' 
                          ? 'bg-gray-100 text-gray-800'
                          : item.status === 'correct'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {item.student_answer}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {item.correct_answer}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {item.status === 'correct' && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <CheckCircleIcon className="h-4 w-4 mr-1" />
                          Correct
                        </span>
                      )}
                      {item.status === 'incorrect' && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          <XCircleIcon className="h-4 w-4 mr-1" />
                          Wrong
                        </span>
                      )}
                      {item.status === 'unanswered' && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          <MinusCircleIcon className="h-4 w-4 mr-1" />
                          Unanswered
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-center space-x-4">
        <Link
          to="/student/dashboard"
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Back to Dashboard
        </Link>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Print Results
        </button>
      </div>
    </div>
  );
};

export default ViewResult;