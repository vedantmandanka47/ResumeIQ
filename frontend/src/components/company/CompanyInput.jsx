import { useState } from 'react';
import Button from '../common/Button';

export default function CompanyInput({ onResearch, loading }) {
  const [companyName, setCompanyName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (companyName.trim()) {
      onResearch(companyName.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="company-input-form">
      <input
        type="text"
        className="company-input__field"
        placeholder="Enter company name..."
        value={companyName}
        onChange={(e) => setCompanyName(e.target.value)}
        disabled={loading}
      />
      <Button 
        type="submit" 
        variant="secondary" 
        loading={loading}
        disabled={!companyName.trim()}
      >
        {loading ? `Researching ${companyName}...` : 'Research →'}
      </Button>
    </form>
  );
}
