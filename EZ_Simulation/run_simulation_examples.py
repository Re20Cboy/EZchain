#!/usr/bin/env python3
"""
Example script demonstrating transaction injection simulation
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Simulation.TransactionInjector import TransactionInjector, SimulationConfig


def run_basic_simulation():
    """Run a basic transaction injection simulation"""
    print("Running Basic Transaction Injection Simulation")
    print("=" * 50)
    
    # Create configuration for basic simulation
    config = SimulationConfig(
        num_senders=3,
        num_transactions_per_batch=2,
        num_batches=5,
        injection_interval=0.2,
        validation_enabled=False,  # Disabled for demo
        signature_enabled=False,  # Simplified for demo
        duplicate_probability=0.0,
        invalid_probability=0.0
    )
    
    # Create injector and run simulation
    injector = TransactionInjector(config)
    
    try:
        stats = injector.run_simulation()
        return stats
    finally:
        injector.cleanup()


def run_stress_test():
    """Run a stress test with more transactions"""
    print("\nRunning Stress Test Simulation")
    print("=" * 50)
    
    config = SimulationConfig(
        num_senders=5,
        num_transactions_per_batch=5,
        num_batches=10,
        injection_interval=0.1,
        validation_enabled=False,
        signature_enabled=False,
        duplicate_probability=0.05,
        invalid_probability=0.02
    )
    
    injector = TransactionInjector(config)
    
    try:
        stats = injector.run_simulation()
        return stats
    finally:
        injector.cleanup()


def run_validation_test():
    """Run a test focusing on validation scenarios"""
    print("\nRunning Validation Test Simulation")
    print("=" * 50)
    
    config = SimulationConfig(
        num_senders=2,
        num_transactions_per_batch=1,
        num_batches=8,
        injection_interval=0.3,
        validation_enabled=False,
        signature_enabled=False,
        duplicate_probability=0.2,  # Higher chance of duplicates
        invalid_probability=0.25   # Higher chance of invalid transactions
    )
    
    injector = TransactionInjector(config)
    
    try:
        stats = injector.run_simulation()
        return stats
    finally:
        injector.cleanup()


def run_custom_simulation():
    """Run a custom simulation with user-defined parameters"""
    print("\nRunning Custom Simulation")
    print("=" * 50)
    
    # Get user input (with defaults)
    try:
        num_senders = int(input("Number of senders (default 3): ") or "3")
        num_batches = int(input("Number of batches (default 5): ") or "5")
        tx_per_batch = int(input("Transactions per batch (default 2): ") or "2")
        interval = float(input("Injection interval in seconds (default 0.2): ") or "0.2")
    except ValueError:
        print("Invalid input, using defaults")
        num_senders, num_batches, tx_per_batch, interval = 3, 5, 2, 0.2
    
    config = SimulationConfig(
        num_senders=num_senders,
        num_transactions_per_batch=tx_per_batch,
        num_batches=num_batches,
        injection_interval=interval,
        validation_enabled=False,
        signature_enabled=False,
        duplicate_probability=0.05,
        invalid_probability=0.02
    )
    
    injector = TransactionInjector(config)
    
    try:
        stats = injector.run_simulation()
        return stats
    finally:
        injector.cleanup()


def main():
    """Main function to run different simulation scenarios"""
    print("Transaction Injection Simulation Examples")
    print("=" * 60)
    
    while True:
        print("\nChoose a simulation scenario:")
        print("1. Basic Simulation")
        print("2. Stress Test")
        print("3. Validation Test")
        print("4. Custom Simulation")
        print("5. Run All Tests")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == '0':
            print("Exiting...")
            break
        elif choice == '1':
            run_basic_simulation()
        elif choice == '2':
            run_stress_test()
        elif choice == '3':
            run_validation_test()
        elif choice == '4':
            run_custom_simulation()
        elif choice == '5':
            print("Running all simulation tests...")
            run_basic_simulation()
            run_stress_test()
            run_validation_test()
            print("All tests completed!")
        else:
            print("Invalid choice, please try again")
        
        if choice != '0':
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()