import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

export default function SubmitComplaint() {
  const navigate = useNavigate();
  
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [categoryError, setCategoryError] = useState(null);

  const [formData, setFormData] = useState({
    category_id: '',
    description: '',
    state: '',
    district: '',
    google_maps_url: '',
    location_address: '',
    inconvenience_details: '',
    expected_solution: ''
  });
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  const [status, setStatus] = useState('idle'); // idle, submitting, success, error
  const [submitError, setSubmitError] = useState(null);
  const [successData, setSuccessData] = useState(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setLoadingCategories(true);
        const res = await api.get('/categories/');
        setCategories(Array.isArray(res) ? res : (res.results || []));
      } catch (err) {
        setCategoryError('Failed to load categories. Please refresh the page.');
      } finally {
        setLoadingCategories(false);
      }
    };
    fetchCategories();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, idx) => idx !== indexToRemove));
  };

  const validateForm = () => {
    if (!formData.category_id) return 'Please select a category.';
    if (formData.description.trim().length < 10) return 'Description must be at least 10 characters.';
    if (!formData.state.trim()) return 'State is required.';
    if (!formData.district.trim()) return 'District is required.';
    if (!formData.google_maps_url.trim()) return 'Google Maps URL is required.';
    try {
      new URL(formData.google_maps_url);
    } catch {
      return 'Please enter a valid Google Maps URL.';
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);

    const validationError = validateForm();
    if (validationError) {
      setSubmitError(validationError);
      return;
    }

    try {
      setStatus('submitting');
      
      const payload = new FormData();
      Object.entries(formData).forEach(([key, value]) => {
        if (value.trim() !== '') {
          payload.append(key, value.trim());
        }
      });
      
      files.forEach(file => {
        payload.append('attachments', file);
      });

      const res = await api.post('/complaints/', payload);
      setSuccessData(res);
      setStatus('success');
    } catch (err) {
      setSubmitError(err.data?.detail || err.message || 'An error occurred while submitting.');
      setStatus('error');
    }
  };

  if (status === 'success' && successData) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 'var(--sp-xl)' }}>
        <CheckCircleSvg size={48} color="var(--success)" />
        <h2 style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-sm)' }}>Issue submitted successfully</h2>
        <p style={{ color: 'var(--text-muted)' }}>Your complaint has been registered.</p>
        
        <div style={{ margin: 'var(--sp-lg) 0', padding: 'var(--sp-md)', background: 'var(--bg-default)', borderRadius: 'var(--radius)' }}>
          <p style={{ fontSize: 12, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 4 }}>Complaint Number</p>
          <p style={{ fontSize: 24, fontWeight: 'bold' }}>{successData.complaint_number}</p>
        </div>

        <div style={{ display: 'flex', gap: 'var(--sp-md)', justifyContent: 'center' }}>
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
          <button className="btn btn-primary" onClick={() => navigate(`/complaints/${successData.id}`)}>View Complaint</button>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--sp-lg)' }}>
        <h2 className="section-title" style={{ fontSize: 24 }}>Report a Civic Issue</h2>
        <p className="page-subtitle">Tell us what needs attention.</p>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '0 0 var(--sp-lg) 0' }} />

      {submitError && (
        <div className="alert alert-error" style={{ marginBottom: 'var(--sp-lg)' }}>
          {submitError}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-lg)' }}>
        
        {/* Category */}
        <div className="form-group">
          <label className="form-label">Issue Category <span style={{ color: 'var(--error)' }}>*</span></label>
          {loadingCategories ? (
            <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>Loading categories...</p>
          ) : categoryError ? (
            <p style={{ fontSize: 14, color: 'var(--error)' }}>{categoryError}</p>
          ) : (
            <select
              className="form-control"
              name="category_id"
              value={formData.category_id}
              onChange={handleChange}
              disabled={status === 'submitting'}
            >
              <option value="">Select category</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          )}
        </div>

        {/* Description */}
        <div className="form-group">
          <label className="form-label">Description <span style={{ color: 'var(--error)' }}>*</span></label>
          <textarea
            className="form-control"
            name="description"
            rows={5}
            placeholder="Describe the issue clearly. Mention what happened, where it is located, and anything that may help the responsible department understand the problem."
            value={formData.description}
            onChange={handleChange}
            disabled={status === 'submitting'}
          />
        </div>
        
        {/* Additional Details */}
        <div className="form-group">
          <label className="form-label">Inconvenience Caused (Optional)</label>
          <textarea
            className="form-control"
            name="inconvenience_details"
            rows={2}
            placeholder="How does this issue affect you or the community?"
            value={formData.inconvenience_details}
            onChange={handleChange}
            disabled={status === 'submitting'}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Expected Solution (Optional)</label>
          <textarea
            className="form-control"
            name="expected_solution"
            rows={2}
            placeholder="What action are you expecting?"
            value={formData.expected_solution}
            onChange={handleChange}
            disabled={status === 'submitting'}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-md)' }}>
          <div className="form-group">
            <label className="form-label">State <span style={{ color: 'var(--error)' }}>*</span></label>
            <input
              type="text"
              className="form-control"
              name="state"
              placeholder="e.g. Kerala"
              value={formData.state}
              onChange={handleChange}
              disabled={status === 'submitting'}
            />
          </div>
          <div className="form-group">
            <label className="form-label">District <span style={{ color: 'var(--error)' }}>*</span></label>
            <input
              type="text"
              className="form-control"
              name="district"
              placeholder="e.g. Ernakulam"
              value={formData.district}
              onChange={handleChange}
              disabled={status === 'submitting'}
            />
          </div>
        </div>
        
        <div className="form-group">
          <label className="form-label">Street Address / Landmark (Optional)</label>
          <input
            type="text"
            className="form-control"
            name="location_address"
            placeholder="e.g. Near Central Park, MG Road"
            value={formData.location_address}
            onChange={handleChange}
            disabled={status === 'submitting'}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Google Maps Location <span style={{ color: 'var(--error)' }}>*</span></label>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--sp-sm)' }}>
            Paste the shareable link from Google Maps (e.g. https://maps.app.goo.gl/... or https://www.google.com/maps/...)
          </p>
          <input
            type="url"
            className="form-control"
            name="google_maps_url"
            placeholder="https://..."
            value={formData.google_maps_url}
            onChange={handleChange}
            disabled={status === 'submitting'}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Evidence</label>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 'var(--sp-sm)' }}>
            Upload photos or documents to help verify the issue.
          </p>
          <button 
            type="button" 
            className="btn btn-secondary" 
            onClick={() => fileInputRef.current?.click()}
            disabled={status === 'submitting'}
          >
            <UploadSvg size={16} style={{ marginRight: 8 }} />
            Upload Photos / Files
          </button>
          <input 
            type="file" 
            multiple 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            style={{ display: 'none' }} 
            disabled={status === 'submitting'}
            accept="image/*,video/*,.pdf,.doc,.docx"
          />
          
          {files.length > 0 && (
            <div style={{ marginTop: 'var(--sp-md)' }}>
              <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 'var(--sp-xs)' }}>Selected files:</p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {files.map((file, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-default)', padding: '6px 12px', borderRadius: 4, fontSize: 14 }}>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '80%' }}>
                      {file.name}
                    </span>
                    <button 
                      type="button" 
                      onClick={() => removeFile(idx)} 
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
                      disabled={status === 'submitting'}
                    >
                      &times;
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: 'var(--sp-md) 0' }} />

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--sp-md)' }}>
          <button type="button" className="btn btn-ghost" onClick={() => navigate('/dashboard')} disabled={status === 'submitting'}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={status === 'submitting' || loadingCategories}>
            {status === 'submitting' ? 'Submitting...' : 'Submit Issue'}
          </button>
        </div>
      </form>
    </div>
  );
}

function CheckCircleSvg({ size = 24, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block' }}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function UploadSvg({ size = 20, style = {} }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={style}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}
