// cordic_pipe.v
// 12-Stage Pipelined CORDIC for Sine/Cosine Generation
// Input angle: 16-bit signed symmetric integer mapped to [-180, 180] degrees.
// Outputs: 16-bit signed Q1.15 fraction format (where 16'h7FFF ~= 1.0, 16'h8000 ~= -1.0)

module cordic_pipe (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [15:0] angle_in, // Input angle [-pi, pi] mapped to [16'h8000, 16'h7FFF]
    output reg  [15:0] sin_out,  // Q1.15 format
    output reg  [15:0] cos_out   // Q1.15 format
);

    // CORDIC gain scaling factor 1/K = 0.60725293500888125
    // Expressed in 16-bit Q1.15: 0.60725 * 32768 = 19898 (16'h4DBD)
    localparam signed [15:0] INITIAL_X = 16'h4DBD; 
    localparam signed [15:0] INITIAL_Y = 16'h0000;

    // Pipeline registers for coordinates (X, Y) and residual Phase (Z)
    reg signed [15:0] x_reg [0:12];
    reg signed [15:0] y_reg [0:12];
    reg signed [15:0] z_reg [0:12];

    // Stage 0: Quadrant Mapping (maps target angle to first/fourth quadrants)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_reg[0] <= 16'h0;
            y_reg[0] <= 16'h0;
            z_reg[0] <= 16'h0;
        end else begin
            // Check if angle is in Quadrant 2 or 3 (Left half plane)
            if (angle_in[15] ^ angle_in[14]) begin 
                // Quadrant 2 or 3: Rotate by 180 degrees
                x_reg[0] <= -INITIAL_X;
                y_reg[0] <= -INITIAL_Y;
                z_reg[0] <= angle_in - 16'h8000; // Adds/subtracts 180 deg in 2's complement
            end else begin
                // Quadrant 1 or 4: Leave as is
                x_reg[0] <= INITIAL_X;
                y_reg[0] <= INITIAL_Y;
                z_reg[0] <= angle_in;
            end
        end
    end

    // Function to get ATAN look-up values safely at elaboration time
    function signed [15:0] get_atan_val(input integer stage);
        case(stage)
            0:  get_atan_val = 16'h2000; // atan(2^0)  = 45.000 deg
            1:  get_atan_val = 16'h12E4; // atan(2^-1) = 26.565 deg
            2:  get_atan_val = 16'h09FB; // atan(2^-2) = 14.036 deg
            3:  get_atan_val = 16'h0511; // atan(2^-3) =  7.125 deg
            4:  get_atan_val = 16'h028B; // atan(2^-4) =  3.576 deg
            5:  get_atan_val = 16'h0145; // atan(2^-5) =  1.790 deg
            6:  get_atan_val = 16'h00A3; // atan(2^-6) =  0.895 deg
            7:  get_atan_val = 16'h0051; // atan(2^-7) =  0.448 deg
            8:  get_atan_val = 16'h0029; // atan(2^-8) =  0.224 deg
            9:  get_atan_val = 16'h0014; // atan(2^-9) =  0.112 deg
            10: get_atan_val = 16'h000A; // atan(2^-10)=  0.056 deg
            11: get_atan_val = 16'h0005; // atan(2^-11)=  0.028 deg
            default: get_atan_val = 16'h0000;
        endcase
    endfunction

    // Stages 1 to 12: Micro-rotations
    genvar i;
    generate
        for (i = 0; i < 12; i = i + 1) begin : cordic_pipeline_stages
            wire signed [15:0] current_atan = get_atan_val(i);
            
            // Explicitly cast sliced array signals to signed to force arithmetic sign-extension
            wire signed [15:0] x_shifted = $signed(x_reg[i]) >>> i;
            wire signed [15:0] y_shifted = $signed(y_reg[i]) >>> i;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    x_reg[i+1] <= 16'h0;
                    y_reg[i+1] <= 16'h0;
                    z_reg[i+1] <= 16'h0;
                end else begin
                    if (z_reg[i][15] == 1'b1) begin // Negative residual angle (rotate clockwise)
                        x_reg[i+1] <= x_reg[i] + y_shifted;
                        y_reg[i+1] <= y_reg[i] - x_shifted;
                        z_reg[i+1] <= z_reg[i] + current_atan;
                    end else begin                  // Positive residual angle (rotate counter-clockwise)
                        x_reg[i+1] <= x_reg[i] - y_shifted;
                        y_reg[i+1] <= y_reg[i] + x_shifted;
                        z_reg[i+1] <= z_reg[i] - current_atan;
                    end
                end
            end
        end
    endgenerate

    // Outputs mapped directly to the final pipeline stage
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sin_out <= 16'h0;
            cos_out <= 16'h0;
        end else begin
            sin_out <= y_reg[12];
            cos_out <= x_reg[12];
        end
    end

endmodule
