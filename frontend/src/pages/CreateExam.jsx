import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { PlusIcon, MinusIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import { examAPI } from '../utils/api';

const CreateExam = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    exam_id: '',
    title: '',
    description: '',
    total_questions: 10,
    number_of_choices: 4,
    max_marks: 10,
  });
  const [answerKey, setAnswerKey] = useState(() => {
    const initial = {};
    for (let i = 1; i <= 10; i++) {
      initial[i.toString()] = 'A';
    }
    return initial;
  });

  // Generate choices based on number_of_choices
  const getAllChoices = () => {
    return Array.from({ length: Math.max(5, formData.number_of_choices) }, (_, i) => String.fromCharCode(65 + i));
  };
  
  const getActiveChoices = () => {
    return Array.from({ length: formData.number_of_choices }, (_, i) => String.fromCharCode(65 + i));
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    const newValue = ['total_questions', 'max_marks', 'number_of_choices'].includes(name) 
      ? parseInt(value) || 0 
      : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Update answer key when total questions or number of choices changes
    if (name === 'total_questions') {
      const newTotal = parseInt(value) || 0;
      const newAnswerKey = {};
      for (let i = 1; i <= newTotal; i++) {
        newAnswerKey[i.toString()] = answerKey[i.toString()] || 'A';
      }
      setAnswerKey(newAnswerKey);
    }
    
    // Reset answer key if number of choices changes and any answer is now invalid
    if (name === 'number_of_choices') {
      const newChoices = parseInt(value) || 4;
      const validChoices = Array.from({ length: newChoices }, (_, i) => String.fromCharCode(65 + i));
      const newAnswerKey = { ...answerKey };
      
      Object.keys(newAnswerKey).forEach(key => {
        if (!validChoices.includes(newAnswerKey[key])) {
          newAnswerKey[key] = 'A'; // Reset to A if current choice is invalid
        }
      });
      
      setAnswerKey(newAnswerKey);
    }
  };

  const handleAnswerChange = (questionNum, answer) => {
    setAnswerKey(prev => ({
      ...prev,
      [questionNum.toString()]: answer
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.exam_id.trim()) {
      toast.error('Exam ID is required');
      return;
    }

    if (!formData.title.trim()) {
      toast.error('Exam title is required');
      return;
    }

    if (formData.total_questions < 1 || formData.total_questions > 200) {
      toast.error('Total questions must be between 1 and 200');
      return;
    }

    if (formData.max_marks < 1) {
      toast.error('Maximum marks must be at least 1');
      return;
    }

    // Validate that all questions have answers
    for (let i = 1; i <= formData.total_questions; i++) {
      if (!answerKey[i.toString()]) {
        toast.error(`Please set an answer for question ${i}`);
        return;
      }
    }

    setLoading(true);

    try {
      const examData = {
        ...formData,
        answer_key: answerKey
      };

      await examAPI.create(examData);
      toast.success('Exam created successfully!');
      navigate('/teacher/dashboard');
    } catch (error) {
      console.error('Failed to create exam:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create exam';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Generate answer key grid
  const generateAnswerKeyGrid = () => {
    const questions = [];
    const activeChoices = getActiveChoices();
    
    for (let i = 1; i <= formData.total_questions; i++) {
      questions.push(
        <div key={i} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-md">
          <div className="w-12 text-sm font-medium text-gray-700">Q{i}:</div>
          <div className="flex space-x-2">
            {activeChoices.map(choice => (
              <label key={choice} className="flex items-center">
                <input
                  type="radio"
                  name={`question_${i}`}
                  value={choice}
                  checked={answerKey[i.toString()] === choice}
                  onChange={() => handleAnswerChange(i, choice)}
                  className="mr-1 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm">{choice}</span>
              </label>
            ))}
          </div>
        </div>
      );
    }
    return questions;
  };

  const generateQuickFill = (choice) => {
    const newAnswerKey = {};
    for (let i = 1; i <= formData.total_questions; i++) {
      newAnswerKey[i.toString()] = choice;
    }
    setAnswerKey(newAnswerKey);
  };

  const generateRandomFill = () => {
    const activeChoices = getActiveChoices();
    const newAnswerKey = {};
    for (let i = 1; i <= formData.total_questions; i++) {
      const randomIndex = Math.floor(Math.random() * activeChoices.length);
      newAnswerKey[i.toString()] = activeChoices[randomIndex];
    }
    setAnswerKey(newAnswerKey);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center">
          <BookOpenIcon className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Create New Exam</h1>
            <p className="mt-2 text-gray-600">Set up a new exam with questions and answer key</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="exam_id" className="block text-sm font-medium text-gray-700">
                Exam ID *
              </label>
              <input
                type="text"
                id="exam_id"
                name="exam_id"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g., MATH101, PHYS201"
                value={formData.exam_id}
                onChange={handleInputChange}
              />
            </div>

            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Exam Title *
              </label>
              <input
                type="text"
                id="title"
                name="title"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="e.g., Mathematics Midterm Exam"
                value={formData.title}
                onChange={handleInputChange}
              />
            </div>

            <div className="md:col-span-2">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Optional description of the exam"
                value={formData.description}
                onChange={handleInputChange}
              />
            </div>

            <div>
              <label htmlFor="total_questions" className="block text-sm font-medium text-gray-700">
                Total Questions *
              </label>
              <input
                type="number"
                id="total_questions"
                name="total_questions"
                required
                min="1"
                max="200"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                value={formData.total_questions}
                onChange={handleInputChange}
              />
            </div>

            <div>
              <label htmlFor="max_marks" className="block text-sm font-medium text-gray-700">
                Maximum Marks *
              </label>
              <input
                type="number"
                id="max_marks"
                name="max_marks"
                required
                min="1"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                value={formData.max_marks}
                onChange={handleInputChange}
              />
            </div>

            <div>
              <label htmlFor="number_of_choices" className="block text-sm font-medium text-gray-700">
                Number of Answer Choices *
              </label>
              <input
                type="number"
                id="number_of_choices"
                name="number_of_choices"
                required
                min="2"
                max="8"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                value={formData.number_of_choices}
                onChange={handleInputChange}
              />
              <p className="mt-1 text-sm text-gray-500">Number of answer options per question (e.g., 4 for A-D, 5 for A-E)</p>
            </div>
          </div>
        </div>

        {/* Answer Key */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Answer Key</h3>
            <div className="flex space-x-2">
              <span className="text-sm text-gray-500">Quick fill:</span>
              <button
                type="button"
                onClick={generateRandomFill}
                className="px-2 py-1 text-xs border border-primary-300 bg-primary-50 text-primary-700 rounded hover:bg-primary-100 font-medium"
              >
                Random
              </button>
              {getActiveChoices().map(choice => (
                <button
                  key={choice}
                  type="button"
                  onClick={() => generateQuickFill(choice)}
                  className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                >
                  All {choice}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {generateAnswerKeyGrid()}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/teacher/dashboard')}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating...
              </div>
            ) : (
              'Create Exam'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateExam;