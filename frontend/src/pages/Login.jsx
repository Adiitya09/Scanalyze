import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { QrCodeIcon, EyeIcon, EyeSlashIcon, UserIcon, KeyIcon, SparklesIcon, HomeIcon } from '@heroicons/react/24/outline';
import { Card, CardContent } from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
 

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(formData);
      if (result.success) {
        toast.success('Welcome back! ', {
          style: {
            background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
            color: '#fff',
          },
        });
        navigate(result.user.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (role) => {
    const credentials = {
      username: role,
      password: 'password'
    };
    
    setFormData(credentials);
    setLoading(true);
    
    try {
      const result = await login(credentials);
      if (result.success) {
        toast.success(`Welcome ${role}! 🚀`, {
          style: {
            background: 'linear-gradient(135deg, #0ea5e9, #d946ef)',
            color: '#fff',
          },
        });
        navigate(result.user.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
      }
    } catch (error) {
      toast.error('Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-primary-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-secondary-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float" style={{animationDelay: '2s'}}></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-accent-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float" style={{animationDelay: '4s'}}></div>
      </div>

      <div className="max-w-md w-full space-y-8 animate-fade-in-up">
        {/* Return to Homepage Button */}
        <div className="flex justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-neutral-700 hover:text-primary-600 bg-white hover:bg-primary-50 backdrop-blur-sm rounded-lg border-2 border-neutral-300 hover:border-primary-400 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            <HomeIcon className="h-5 w-5" />
            Return to Homepage
          </Link>
        </div>

        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-2xl bg-gradient-to-r from-primary-500 to-secondary-500 animate-glow mb-6">
            <QrCodeIcon className="h-8 w-8 text-white animate-float" />
          </div>
          <h1 className="heading-lg font-brand gradient-text mb-1">SCANALYZE</h1>
          <p className="text-neutral-600 mb-2">Smart OMR Evaluator</p>
          <h2 className="heading-md gradient-text mb-2">Welcome Back</h2>
          <p className="text-neutral-600">
            Sign in to continue your journey
          </p>
          <div className="flex items-center justify-center mt-4 space-x-2">
            <div className="flex -space-x-1">
              
            </div>
            
          </div>
        </div>

        {/* Login Form */}
        <Card variant="glass" className="p-8">
          <CardContent className="p-0">
            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                name="username"
                label="Username"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleChange}
                leftIcon={<UserIcon className="h-5 w-5 text-neutral-400" />}
                required
              />

              <Input
                name="password"
                type={showPassword ? 'text' : 'password'}
                label="Password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                leftIcon={<KeyIcon className="h-5 w-5 text-neutral-400" />}
                rightIcon={
                  <button
                    type="button"
                    className="text-neutral-400 hover:text-neutral-600 transition-colors"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                }
                required
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                className="w-full"
              >
                
                Sign In
              </Button>

              <div className="text-center">
                <span className="text-neutral-500 text-sm">Don&apos;t have an account? </span>
                <Link
                  to="/register"
                  className="text-primary-600 hover:text-primary-500 font-semibold text-sm transition-colors"
                >
                  Create one now
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>

      </div>
    </div>
  );
};

export default Login;
