import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  BookOpenIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  EyeIcon,
  TrophyIcon,
  AcademicCapIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { examAPI, studentAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';

const StudentDashboard = () => {
  const [exams, setExams] = useState([]);
  const [studentData, setStudentData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      console.log('Fetching dashboard data...');
      
      // Fetch exams first
      const examsResponse = await examAPI.getAll();
      console.log('Exams response:', examsResponse.data);
      setExams(examsResponse.data);
      
      // Then try to fetch student dashboard data
      try {
        const studentResponse = await studentAPI.getDashboard();
        console.log('Student dashboard response:', studentResponse.data);
        setStudentData(studentResponse.data);
      } catch (studentError) {
        console.log('Student dashboard API error:', studentError);
        // This is expected for students with no results yet or API errors
        setStudentData(null);
      }
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading dashboard..." />;
  }

  const activeExams = exams.filter(exam => exam.is_active);

  const highestExam = studentData?.recent_results?.reduce((prev, curr) =>
  curr.score > prev.score ? curr : prev,
  { score: 0, max_marks: 0 }
  );

  const highestScore = highestExam?.score || 0;
  const totalMarks = highestExam?.max_marks || 0;

  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Student Dashboard</h1>
            <p className="mt-2 text-gray-600">View available exams and upload your OMR sheets</p>
          </div>
          <Link
            to="/student/upload-omr"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
            Upload OMR Sheet
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="bg-blue-500 p-3 rounded-md">
                  <BookOpenIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Available Exams
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {activeExams.length}
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
                <div className="bg-green-500 p-3 rounded-md">
                  <AcademicCapIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Exams Taken
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {studentData?.total_exams_taken || 0}
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
                <div className="bg-purple-500 p-3 rounded-md">
                  <TrophyIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Score
                  </dt>
                  <dd className="text-3xl font-semibold text-gray-900">
                    {studentData?.average_percentage ? `${studentData.average_percentage}%` : 'N/A'}
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
        <div className="bg-yellow-500 p-3 rounded-md">
          <CheckCircleIcon className="h-6 w-6 text-white" />
        </div>
      </div>
      <div className="ml-5 w-0 flex-1">
        <dl>
          <dt className="text-sm font-medium text-gray-500 truncate">
            Highest Score
          </dt>
          <dd className="text-3xl font-semibold text-gray-900">
            {highestScore} / {totalMarks}
          </dd>
        </dl>
      </div>
    </div>
  </div>
</div>

      </div>

      

      {/* Available Exams */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-2xl leading-6 font-bold text-gray-700">Available Exams</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Click on an exam to view details or upload your OMR sheet
          </p>
        </div>

        {activeExams.length === 0 ? (
          <div className="text-center py-12">
            <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No exams available</h3>
            <p className="mt-1 text-sm text-gray-500">
              Check back later for new exams or contact your teacher.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {activeExams.map((exam) => (
              <li key={exam.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BookOpenIcon className="h-8 w-8 text-gray-400" />
                    </div>
                    <div className="ml-4">
                      <h4 className="text-lg font-medium text-gray-900">
                        {exam.title}
                      </h4>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <DocumentTextIcon className="h-4 w-4 mr-1" />
                          Exam ID: <span className="font-mono font-medium ml-1">{exam.exam_id}</span>
                        </span>
                        <span className="flex items-center">
                          <CheckCircleIcon className="h-4 w-4 mr-1" />
                          {exam.total_questions} questions
                        </span>
                        <span className="flex items-center">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          Max marks: {exam.max_marks}
                        </span>
                      </div>
                      {exam.description && (
                        <p className="mt-2 text-sm text-gray-600">{exam.description}</p>
                      )}
                      <p className="mt-1 text-sm text-gray-500">
                        Created: {new Date(exam.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/exam/${exam.exam_id}`}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <EyeIcon className="h-4 w-4 mr-2" />
                      View Details
                    </Link>
                    <Link
                      to={`/student/upload-omr?examId=${exam.exam_id}`}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                      Upload OMR
                    </Link>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

{/* Divider */}
<hr className="my-8 border-t border-gray-300" />

      {/* Previous Results */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md mb-8">
        <div className="px-4 py-5 sm:px-6 flex items-center justify-between">
          <div>
            <h3 className="text-2xl leading-6 font-bold text-gray-700">Your Recent Results</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Review your recent performance and view detailed results.
            </p>
          </div>
        </div>

        {!studentData || !studentData.recent_results || studentData.recent_results.length === 0 ? (
          <div className="text-center py-12">
            <TrophyIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Complete an exam to see your results here.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {studentData.recent_results.map((item) => (
              <li key={item.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                      </div>
                      <div className="ml-4">
                        <h4 className="text-lg font-medium text-gray-900">
                          {item.exam_title}
                        </h4>
                        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <DocumentTextIcon className="h-4 w-4 mr-1" />
                            Exam ID: <span className="font-mono font-medium ml-1">{item.exam_id}</span>
                          </span>
                          <span className="flex items-center">
                            <CheckCircleIcon className="h-4 w-4 mr-1 text-green-500" />
                            Score: <span className="ml-1 font-medium text-gray-900">{item.score}/{item.max_marks}</span>
                          </span>
                          <span className="flex items-center">
                            <TrophyIcon className="h-4 w-4 mr-1 text-yellow-500" />
                            {item.percentage.toFixed(1)}%
                          </span>
                          <span className="flex items-center">
                            <CalendarIcon className="h-4 w-4 mr-1" />
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Quick Start Guide */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <BookOpenIcon className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">How to submit your OMR sheet</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ol className="list-decimal list-inside space-y-1">
                <li>Select an exam from the list above</li>
                <li>Note down the Exam ID</li>
                <li>Fill out your OMR sheet carefully</li>
                <li>Scan or take a clear photo of your OMR sheet</li>
                <li>Click &quot;Upload OMR&quot; and submit your file with roll number</li>
                <li>View your results instantly after processing</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;