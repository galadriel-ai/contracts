// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface IOracle {

    struct Content {
        string contentType;
        string value;
    }

    struct Message {
        string role;
        Content [] content;
    }

    struct OpenAiRequest {
        // "gpt-4-turbo", "gpt-4-turbo-preview" or "gpt-3.5-turbo-1106"
        string model;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 frequencyPenalty;
        // JSON string or empty string
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 presencePenalty;
        // JSON string or empty string
        string responseFormat;
        // 0 for null
        uint seed;
        // empty str for null
        string stop;
        // 0-20, > 20 for null
        uint temperature;
        // 0-100  percentage, > 100 for null
        uint topP;
        // JSON list for tools in OpenAI format, empty for null, names have to match the supported tools
        string tools;
        // "none", "auto" or empty str which defaults to auto on OpenAI side
        string toolChoice;
        string user;
    }

    struct OpenAiResponse {
        string id;

        // either content is an empty str or functionName and functionArguments
        string content;
        string functionName;
        string functionArguments;

        uint64 created;
        string model;
        string systemFingerprint;
        // kind of pointless since its always "chat.completion"?
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }

    struct GroqRequest {
        // "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768" or "gemma-7b-it"
        string model;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 frequencyPenalty;
        // JSON string or empty string
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 presencePenalty;
        // JSON string or empty string
        string responseFormat;
        // 0 for null
        uint seed;
        // empty str for null
        string stop;
        // 0-20, > 20 for null
        uint temperature;
        // 0-100  percentage, > 100 for null
        uint topP;
        string user;
    }

    struct GroqResponse {
        string id;

        string content;

        uint64 created;
        string model;
        string systemFingerprint;
        // kind of pointless since its always "chat.completion"?
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }

    struct LlmRequest {
        // "claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1", "claude-2.0", "claude-instant-1.2"
        string model;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 frequencyPenalty;
        // JSON string or empty string
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20, Mapped to float -2.0 - 2.0. If bigger than 20 then null
        int8 presencePenalty;
        // JSON string or empty string
        string responseFormat;
        // 0 for null
        uint seed;
        // empty str for null
        string stop;
        // 0-20, > 20 for null
        uint temperature;
        // 0-100  percentage, > 100 for null
        uint topP;
        // JSON list for tools in OpenAI format, empty for null, names have to match the supported tools
        string tools;
        // "none", "auto" or empty str which defaults to auto on OpenAI side
        string toolChoice;
        string user;
    }

    struct LlmResponse {
        string id;

        // either content is an empty str or functionName and functionArguments
        string content;
        string functionName;
        string functionArguments;

        uint64 created;
        string model;
        string systemFingerprint;
        // kind of pointless since its always "chat.completion"?
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }


    struct KnowledgeBaseQueryRequest {
        string cid;
        string query;
        uint32 num_documents;
    }

    function createLlmCall(
        uint promptId
    ) external returns (uint);

    function createLlmCall(
        uint promptId,
        LlmRequest memory request
    ) external returns (uint);

    function createGroqLlmCall(
        uint promptId,
        GroqRequest memory request
    ) external returns (uint);

    function createOpenAiLlmCall(
        uint promptId,
        OpenAiRequest memory request
    ) external returns (uint);

    function createFunctionCall(
        uint functionCallbackId,
        string memory functionType,
        string memory functionInput
    ) external returns (uint i);

    function createKnowledgeBaseQuery(
        uint kbQueryCallbackId,
        string memory cid,
        string memory query,
        uint32 num_documents
    ) external returns (uint i);
}