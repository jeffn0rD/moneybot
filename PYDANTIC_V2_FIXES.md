# Pydantic V2 Compatibility Fixes

## Issues Fixed

### 1. Pydantic Import Error Fixed
- **Error**: `pydantic.errors.PydanticImportError: BaseSettings has been moved to the pydantic-settings package`
- **Solution**: Updated imports to use `pydantic-settings` package

### 2. Field Definition Updates
- **Change**: Updated Field definitions to use alias instead of env parameter
- **Files**: libs/utils/config.py

### 3. Validator Updates
- **Change**: Updated validator imports to use field_validator
- **Files**: libs/schemas/models.py

## Files Updated
- ✅ libs/utils/config.py - Fixed BaseSettings import and Field definitions
- ✅ libs/schemas/models.py - Updated validator import

## Verification
All Python files now compile successfully with Pydantic v2.