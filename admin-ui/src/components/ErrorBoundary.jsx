import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ error, errorInfo });
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-8 text-white bg-red-900/50 rounded-lg">
                    <h1 className="text-xl font-bold mb-4">Something went wrong.</h1>
                    <p className="font-mono text-sm bg-black/50 p-4 rounded">
                        {this.state.error && this.state.error.toString()}
                    </p>
                    <pre className="mt-4 text-xs opacity-70 overflow-auto max-h-40">
                        {this.state.errorInfo && this.state.errorInfo.componentStack}
                    </pre>
                </div>
            );
        }
        return this.props.children;
    }
}

export default ErrorBoundary;
