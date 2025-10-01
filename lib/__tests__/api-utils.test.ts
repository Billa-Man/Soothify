import { ApiError, API_ERRORS, successResponse, errorResponse, validateQueryParams } from '../api-utils';

describe('API Utils', () => {
  describe('ApiError', () => {
    it('should create ApiError with correct properties', () => {
      const error = new ApiError(400, 'Bad request', 'BAD_REQUEST');

      expect(error.statusCode).toBe(400);
      expect(error.message).toBe('Bad request');
      expect(error.code).toBe('BAD_REQUEST');
      expect(error.name).toBe('ApiError');
    });

    it('should inherit from Error', () => {
      const error = new ApiError(500, 'Internal server error');

      expect(error).toBeInstanceOf(Error);
      expect(error.stack).toBeDefined();
    });
  });

  describe('API_ERRORS', () => {
    it('should create BAD_REQUEST error with custom message', () => {
      const error = API_ERRORS.BAD_REQUEST('Custom bad request message');

      expect(error.statusCode).toBe(400);
      expect(error.message).toBe('Custom bad request message');
      expect(error.code).toBe('BAD_REQUEST');
    });

    it('should create errors with default messages', () => {
      const badRequest = API_ERRORS.BAD_REQUEST();
      const notFound = API_ERRORS.NOT_FOUND();

      expect(badRequest.message).toBe('Bad request');
      expect(notFound.message).toBe('Not found');
    });
  });

  describe('successResponse', () => {
    it('should create success response with data and message', () => {
      const data = { id: 1, name: 'test' };
      const response = successResponse(data, 'Success message');

      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toBe('application/json');
    });

    it('should create success response with data only', () => {
      const data = [1, 2, 3];
      const response = successResponse(data);

      expect(response.status).toBe(200);
    });
  });

  describe('errorResponse', () => {
    it('should create error response from ApiError', () => {
      const apiError = new ApiError(404, 'Not found', 'NOT_FOUND');
      const response = errorResponse(apiError);

      expect(response.status).toBe(404);
      expect(response.headers.get('content-type')).toBe('application/json');
    });

    it('should create error response from generic Error', () => {
      const error = new Error('Generic error');
      const response = errorResponse(error);

      expect(response.status).toBe(500);
    });

    it('should create error response from unknown error', () => {
      const response = errorResponse('Unknown error');

      expect(response.status).toBe(500);
    });
  });

  describe('validateQueryParams', () => {
    it('should validate required parameters', () => {
      const searchParams = new URLSearchParams('name=test&age=25');
      const schema = {
        name: { required: true },
        age: { required: false },
      };

      const result = validateQueryParams(searchParams, schema);

      expect(result).toEqual({ name: 'test', age: '25' });
    });

    it('should throw error for missing required parameter', () => {
      const searchParams = new URLSearchParams('age=25');
      const schema = {
        name: { required: true },
        age: { required: false },
      };

      expect(() => validateQueryParams(searchParams, schema)).toThrow('name is required');
    });

    it('should validate parameter patterns', () => {
      const searchParams = new URLSearchParams('email=test@example.com&phone=1234567890');
      const schema = {
        email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
        phone: { required: false, pattern: /^\d{10}$/ },
      };

      const result = validateQueryParams(searchParams, schema);

      expect(result).toEqual({ email: 'test@example.com', phone: '1234567890' });
    });

    it('should throw error for invalid pattern', () => {
      const searchParams = new URLSearchParams('email=invalid-email&phone=123');
      const schema = {
        email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
        phone: { required: false, pattern: /^\d{10}$/ },
      };

      expect(() => validateQueryParams(searchParams, schema)).toThrow('phone format is invalid');
    });
  });
});
