"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps {
  value: number[];
  onValueChange: (value: number[]) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ value, onValueChange, min = 0, max = 100, step = 1, className, ...props }, ref) => {
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseInt(event.target.value);
      onValueChange([newValue]);
    };

    return (
      <input
        ref={ref}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0] || 0}
        onChange={handleChange}
        className={cn(
          "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider",
          "focus:outline-none focus:ring-2 focus:ring-blue-500",
          "[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4",
          "[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500",
          "[&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow",
          "[&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:rounded-full",
          "[&::-moz-range-thumb]:bg-blue-500 [&::-moz-range-thumb]:cursor-pointer",
          "[&::-moz-range-thumb]:border-none [&::-moz-range-thumb]:shadow",
          className
        )}
        {...props}
      />
    );
  }
);

Slider.displayName = "Slider";

export { Slider };
