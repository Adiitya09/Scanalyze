import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  BookOpenIcon,
  ClockIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ArrowUpTrayIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { examAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const ViewExam = () => {
  const { examId } = useParams();
  const { user } = useAuth();
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExam();
  }, [examId]);

  const fetchExam = async () => {
    try {
      const response = await examAPI.getById(examId);
      setExam(response.data);
    } catch (error) {
      console.error('Failed to fetch exam:', error);
      toast.error('Failed to load exam details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading exam details..." />;
  }

  if (!exam) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Exam not found</h3>
        <p className="mt-1 text-sm text-gray-500">
          The exam you&apos;re looking for doesn&apos;t exist or is no longer active.
        </p>
        <div className="mt-6">
          <Link
            to={user?.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard'}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Go Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const choices = Array.from({ length: exam?.number_of_choices || 4 }, (_, i) => String.fromCharCode(65 + i));

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BookOpenIcon className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{exam.title}</h1>
              <p className="mt-2 text-gray-600">Exam ID: {exam.exam_id}</p>
            </div>
          </div>
          
          {user?.role === 'student' && (
            <Link
              to={`/student/upload-omr?examId=${exam.exam_id}`}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
              Upload OMR Sheet
            </Link>
          )}

          {user?.role === 'teacher' && exam.teacher_id === user.id && (
            <Link
              to={`/teacher/exam/${exam.exam_id}/statistics`}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              View Statistics
            </Link>
          )}
        </div>
      </div>

      {/* Basic Information */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Exam Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-center">
              <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-sm text-gray-500">Total Questions</p>
                <p className="text-lg font-medium text-gray-900">{exam.total_questions}</p>
              </div>
            </div>
            
            <div className="flex items-center">
              <CheckCircleIcon className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-sm text-gray-500">Maximum Marks</p>
                <p className="text-lg font-medium text-gray-900">{exam.max_marks}</p>
              </div>
            </div>
            
            <div className="flex items-center">
              <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="text-lg font-medium text-gray-900">
                  {new Date(exam.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div className="flex items-center">
              <div className={`h-5 w-5 rounded-full mr-2 ${
                exam.is_active ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <p className="text-lg font-medium text-gray-900">
                  {exam.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </div>

          {exam.description && (
            <div className="mt-6">
              <p className="text-sm text-gray-500 mb-2">Description</p>
              <p className="text-gray-700">{exam.description}</p>
            </div>
          )}
        </div>
      </div>

      {/* Answer Key - Only show to teachers */}
      {user?.role === 'teacher' && exam.teacher_id === user.id && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Answer Key</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: exam.total_questions }, (_, i) => {
                const questionNum = (i + 1).toString();
                const correctAnswer = exam.answer_key[questionNum];
                
                return (
                  <div key={questionNum} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-md">
                    <div className="w-12 text-sm font-medium text-gray-700">
                      Q{questionNum}:
                    </div>
                    <div className="flex space-x-2">
                      {choices.map(choice => (
                        <div
                          key={choice}
                          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-medium ${
                            correctAnswer === choice
                              ? 'border-green-500 bg-green-100 text-green-700'
                              : 'border-gray-300 text-gray-500'
                          }`}
                        >
                          {choice}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Student Instructions */}
      {user?.role === 'student' && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-6">
          <div className="flex">
            <BookOpenIcon className="h-5 w-5 text-blue-400 flex-shrink-0" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Instructions for Students</h3>
              <div className="mt-2 text-sm text-blue-700">
                <ol className="list-decimal list-inside space-y-1">
                  <li>Fill out your OMR sheet carefully using a dark pen or pencil</li>
                  <li>Make sure to fill the bubbles completely</li>
                  <li>Write your roll number clearly on the OMR sheet</li>
                  <li>Take a clear, well-lit photo or scan of your completed sheet</li>
                  <li>Upload the image using the &quot;Upload OMR Sheet&quot; button above</li>
                  <li>You can view your results immediately after processing</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ViewExam;