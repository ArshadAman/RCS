import React, { useState, useEffect } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { surveyQuestions, reviewAnswers } from '../api/api';

export default function Surveys() {
  const { currentCompany } = useCompany();
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [newQuestion, setNewQuestion] = useState({
    question_text: '',
    question_type: 'text',
    is_required: false,
    options: ''
  });

  const questionTypes = [
    { value: 'text', label: 'Text Input' },
    { value: 'textarea', label: 'Long Text' },
    { value: 'radio', label: 'Single Choice' },
    { value: 'checkbox', label: 'Multiple Choice' },
    { value: 'rating', label: 'Rating Scale' },
    { value: 'yes_no', label: 'Yes/No' }
  ];

  useEffect(() => {
    if (currentCompany?.id) {
      loadData();
    }
  }, [currentCompany]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [questionsData, answersData] = await Promise.all([
        surveyQuestions.list(currentCompany.id),
        reviewAnswers.list({ company_id: currentCompany.id })
      ]);

      setQuestions(questionsData.results || questionsData || []);
      setAnswers(answersData.results || answersData || []);
    } catch (err) {
      console.error('Failed to load survey data:', err);
      setError(err.message || 'Failed to load survey data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    
    try {
      const questionData = {
        ...newQuestion,
        company: currentCompany.id,
        options: newQuestion.options ? newQuestion.options.split('\n').filter(opt => opt.trim()) : []
      };

      if (editingQuestion) {
        await surveyQuestions.update(editingQuestion.id, questionData);
      } else {
        await surveyQuestions.create(questionData);
      }

      // Reset form
      setNewQuestion({
        question_text: '',
        question_type: 'text',
        is_required: false,
        options: ''
      });
      setShowCreateForm(false);
      setEditingQuestion(null);
      loadData();
    } catch (err) {
      console.error('Failed to save question:', err);
      alert(err.message || 'Failed to save question');
    }
  };

  const handleEditQuestion = (question) => {
    setEditingQuestion(question);
    setNewQuestion({
      question_text: question.question_text,
      question_type: question.question_type,
      is_required: question.is_required,
      options: Array.isArray(question.options) ? question.options.join('\n') : ''
    });
    setShowCreateForm(true);
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question? All associated answers will also be deleted.')) {
      return;
    }

    try {
      await surveyQuestions.delete(questionId);
      loadData();
    } catch (err) {
      console.error('Failed to delete question:', err);
      alert('Failed to delete question');
    }
  };

  const exportSurveyData = () => {
    try {
      if (!answers.length) {
        alert('No survey data to export');
        return;
      }

      // Prepare CSV data
      const headers = ['Question', 'Answer', 'Review ID', 'Date'];
      const csvContent = [
        headers.join(','),
        ...answers.map(answer => {
          const question = questions.find(q => q.id === answer.question);
          return [
            `"${question?.question_text || 'Unknown Question'}"`,
            `"${(answer.answer_text || '').replace(/"/g, '""')}"`,
            answer.review || 'N/A',
            new Date(answer.created_at || Date.now()).toLocaleDateString()
          ].join(',');
        })
      ].join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `survey-data-${currentCompany.name}-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export survey data:', err);
      alert('Failed to export survey data');
    }
  };

  if (!currentCompany) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">🏢</div>
            <h2 className="text-xl font-semibold text-slate-700 mb-2">No Company Selected</h2>
            <p className="text-slate-500">Please select a company from the dropdown above.</p>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  if (loading) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚡</div>
            <p className="text-slate-600">Loading survey data...</p>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  if (error) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Survey Data</h2>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-extrabold text-slate-900 mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Survey Management
            </h1>
            <p className="text-slate-600">Create and manage dynamic survey questions for {currentCompany.name}</p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={exportSurveyData} className="bg-gradient-to-r from-green-500 to-teal-500">
              📊 Export Data
            </Button>
            <Button 
              onClick={() => setShowCreateForm(true)}
              className="bg-gradient-to-r from-indigo-500 to-purple-500"
            >
              ➕ Add Question
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card gradient>
            <div className="text-3xl mb-2">📋</div>
            <div className="text-2xl font-bold text-slate-800">{questions.length}</div>
            <div className="text-slate-600 text-sm">Total Questions</div>
          </Card>
          <Card gradient>
            <div className="text-3xl mb-2">📝</div>
            <div className="text-2xl font-bold text-slate-800">{answers.length}</div>
            <div className="text-slate-600 text-sm">Total Responses</div>
          </Card>
          <Card gradient>
            <div className="text-3xl mb-2">⚡</div>
            <div className="text-2xl font-bold text-slate-800">
              {questions.filter(q => q.is_required).length}
            </div>
            <div className="text-slate-600 text-sm">Required Questions</div>
          </Card>
          <Card gradient>
            <div className="text-3xl mb-2">📊</div>
            <div className="text-2xl font-bold text-slate-800">
              {answers.length > 0 && questions.length > 0 
                ? Math.round((answers.length / questions.length) * 100) / 100
                : 0
              }
            </div>
            <div className="text-slate-600 text-sm">Avg Responses/Question</div>
          </Card>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Survey Questions */}
        <div className="space-y-6">
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Survey Questions</h3>
            
            {questions.length > 0 ? (
              <div className="space-y-4">
                {questions.map((question, index) => (
                  <div key={question.id} className="p-4 bg-white/50 rounded-lg border border-slate-200">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="bg-indigo-100 text-indigo-800 text-xs font-medium px-2 py-1 rounded">
                            Q{index + 1}
                          </span>
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                            {questionTypes.find(t => t.value === question.question_type)?.label || question.question_type}
                          </span>
                          {question.is_required && (
                            <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded">
                              Required
                            </span>
                          )}
                        </div>
                        <p className="font-medium text-slate-800 mb-2">{question.question_text}</p>
                        
                        {/* Show options for choice-based questions */}
                        {(question.question_type === 'radio' || question.question_type === 'checkbox') && question.options && (
                          <div className="mt-2">
                            <p className="text-sm text-slate-600 mb-1">Options:</p>
                            <ul className="text-sm text-slate-700 ml-4">
                              {Array.isArray(question.options) 
                                ? question.options.map((option, i) => (
                                    <li key={i} className="list-disc">{option}</li>
                                  ))
                                : <li className="list-disc">{question.options}</li>
                              }
                            </ul>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          onClick={() => handleEditQuestion(question)}
                          className="bg-blue-500 hover:bg-blue-600"
                        >
                          ✏️
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDeleteQuestion(question.id)}
                          className="bg-red-500 hover:bg-red-600"
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                    
                    {/* Response count for this question */}
                    <div className="text-sm text-slate-500">
                      {answers.filter(a => a.question === question.id).length} responses
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">📋</div>
                <h4 className="text-lg font-semibold text-slate-700 mb-2">No Survey Questions</h4>
                <p className="text-slate-500 mb-4">Create your first survey question to start collecting structured feedback.</p>
                <Button 
                  onClick={() => setShowCreateForm(true)}
                  className="bg-gradient-to-r from-indigo-500 to-purple-500"
                >
                  ➕ Create First Question
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Survey Responses */}
        <div className="space-y-6">
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Recent Responses</h3>
            
            {answers.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {answers.slice(0, 20).map((answer) => {
                  const question = questions.find(q => q.id === answer.question);
                  return (
                    <div key={answer.id} className="p-3 bg-white/50 rounded-lg border border-slate-200">
                      <div className="mb-2">
                        <p className="text-sm font-medium text-slate-700">
                          {question?.question_text || 'Unknown Question'}
                        </p>
                        <p className="text-sm text-slate-500">
                          Type: {question?.question_type || 'unknown'}
                        </p>
                      </div>
                      <p className="text-slate-800 font-medium">{answer.answer_text}</p>
                      <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                        <span>Review ID: {answer.review}</span>
                        <span>{new Date(answer.created_at || Date.now()).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
                
                {answers.length > 20 && (
                  <div className="text-center pt-4">
                    <p className="text-sm text-slate-500">
                      Showing 20 of {answers.length} responses
                    </p>
                    <Button size="sm" onClick={exportSurveyData} className="mt-2">
                      📊 Export All Data
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">📊</div>
                <h4 className="text-lg font-semibold text-slate-700 mb-2">No Responses Yet</h4>
                <p className="text-slate-500">Responses will appear here once customers start filling out your survey questions.</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Create/Edit Question Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-96 overflow-y-auto">
            <h3 className="text-xl font-bold text-slate-900 mb-4">
              {editingQuestion ? 'Edit Question' : 'Create New Question'}
            </h3>
            
            <form onSubmit={handleCreateQuestion} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Question Text *</label>
                <textarea
                  value={newQuestion.question_text}
                  onChange={(e) => setNewQuestion(prev => ({ ...prev, question_text: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows="2"
                  required
                  placeholder="What would you like to ask?"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Question Type</label>
                <select
                  value={newQuestion.question_type}
                  onChange={(e) => setNewQuestion(prev => ({ ...prev, question_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  {questionTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              {(newQuestion.question_type === 'radio' || newQuestion.question_type === 'checkbox') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Options (one per line)
                  </label>
                  <textarea
                    value={newQuestion.options}
                    onChange={(e) => setNewQuestion(prev => ({ ...prev, options: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    rows="3"
                    placeholder="Option 1&#10;Option 2&#10;Option 3"
                  />
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_required"
                  checked={newQuestion.is_required}
                  onChange={(e) => setNewQuestion(prev => ({ ...prev, is_required: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                />
                <label htmlFor="is_required" className="ml-2 block text-sm text-slate-700">
                  Required question
                </label>
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingQuestion(null);
                    setNewQuestion({
                      question_text: '',
                      question_type: 'text',
                      is_required: false,
                      options: ''
                    });
                  }}
                  className="flex-1 bg-slate-500 hover:bg-slate-600"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-500"
                >
                  {editingQuestion ? 'Update' : 'Create'} Question
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </SaaSLayout>
  );
}
