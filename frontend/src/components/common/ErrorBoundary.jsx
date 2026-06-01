import { Component } from 'react';
import ErrorBlock from './ErrorBlock';

/**
 * ErrorBoundary — Catches render errors and displays an ErrorBlock instead of crashing.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px' }}>
          <ErrorBlock 
            message={this.state.error?.message || 'An unexpected error occurred during render.'} 
            onRetry={() => this.setState({ hasError: false, error: null })} 
          />
        </div>
      );
    }
    return this.props.children;
  }
}
